import os
import re
import shlex
import subprocess
import sys
from functools import cached_property
from pathlib import Path
from typing import Any

from pydantic import BaseModel, Field
from sweagent.environment.sql_env import SQLEnvironmentConfig
from sweagent.tools.bundle import Bundle

# from sweagent.tools.sql_commands import Argument, Command
from sweagent.tools.commands import Command
from sweagent.tools.parsing import FunctionCallingParser, JsonParser, ParseFunction
from sweagent.tools.utils import generate_command_docs
from sweagent.utils.log import get_logger


def _expand_ansi_c_quotes(s: str) -> str:
    """Convert bash ANSI-C $'...' quoting to POSIX-compatible quoting for shlex.
    Used for SQL tool call parsing.

    shlex.split() is POSIX-only and mishandles bash's $'...' quoting in two ways:
      1. It treats $'foo' as literal-$ concatenated with POSIX-quoted 'foo', yielding '$foo'.
      2. If the ANSI-C content contains \\' (escaped apostrophe), shlex raises ValueError
         because POSIX single-quotes cannot contain a literal single-quote.

    This preprocessor expands every $'...' sequence to its actual string content, then
    re-quotes it with shlex.quote() so the result is valid POSIX for shlex.split().

    Examples:
        $'financial'              -> 'financial'
        $'unemployment rate'      -> 'unemployment rate'
        $'What\\'s the policy?'   -> "What's the policy?"
    """
    _ansi_escape_map = {
        "n": "\n", "r": "\r", "t": "\t", "a": "\a",
        "b": "\b", "f": "\f", "v": "\v",
        "0": "\0", "'": "'", "\\": "\\",
    }
    result: list[str] = []
    i = 0
    while i < len(s):
        if s[i] == "$" and i + 1 < len(s) and s[i + 1] == "'":
            j = i + 2
            content: list[str] = []
            while j < len(s):
                if s[j] == "\\" and j + 1 < len(s):
                    content.append(_ansi_escape_map.get(s[j + 1], s[j + 1]))
                    j += 2
                elif s[j] == "'":
                    j += 1
                    break
                else:
                    content.append(s[j])
                    j += 1
            result.append(shlex.quote("".join(content)))
            i = j
        else:
            result.append(s[i])
            i += 1
    return "".join(result)


class SQLToolConfig(BaseModel):
    """
    Configuration for preparing SQL tools
    """

    tool_dir: str = "tools/"
    bundles: list[Bundle] = Field(default_factory=list)
    enable_bash_tool: bool = False
    parse_function: ParseFunction = Field(default_factory=FunctionCallingParser)
    propagate_env_variables: list[str] = []
    env_variables: dict[str, Any] = {}
    submit_command: str = "submit_sql"
    execution_timeout: int = (
        1200  # 20 minutes per action (SentenceTransformer model load on EFS can be slow)
    )
    total_execution_timeout: int = 10800  # 3 hours for whole trajectory
    max_consecutive_execution_timeouts: int = (
        5  # 5 consecutive timeouts per action before giving up
    )
    multi_line_command_endings: dict[str, str] = {}
    format_error_template: str | None = None
    submit_command_end_name: str | None = None

    @cached_property
    def state_commands(self) -> list[str]:
        return [bundle.state_command for bundle in self.bundles if bundle.state_command]

    @cached_property
    def commands(self) -> list[Command]:
        loaded_commands = []
        for bundle in self.bundles:
            loaded_commands.extend(bundle.commands)
        return loaded_commands

    @cached_property
    def command_docs(self) -> str:
        docs = []
        for cmd in self.commands:
            docs.append(f"Command: {cmd.name}")
            docs.append(f"  Description: {cmd.docstring}")
            if cmd.arguments:
                docs.append("  Arguments:")
                for arg in cmd.arguments:
                    req = "required" if arg.required else "optional"
                    docs.append(f"    - {arg.name} ({arg.type}, {req}): {arg.description}")
            docs.append("-" * 20)
        return "\n".join(docs)

    @cached_property
    def tools(self) -> list[dict]:
        return [command.get_function_calling_tool() for command in self.commands]

    @cached_property
    def use_function_calling(self) -> bool:
        return isinstance(self.parse_function, FunctionCallingParser)

    def model_post_init(self, __context):
        # for caching:
        commands = self.commands
        multi_line_command_endings = {
            command.name: command.end_name for command in commands if command.end_name is not None
        }
        self.tools

        # assert not self.enable_bash_tool and parse_function is FunctionCallingParser or JsonParser
        if not self.enable_bash_tool and not (
            isinstance(self.parse_function, FunctionCallingParser)
            or isinstance(self.parse_function, JsonParser)
        ):
            msg = (
                "Bash tool can only be disabled if function_calling parser or json parser is used."
            )
            raise ValueError(msg)

        self.multi_line_command_endings = multi_line_command_endings
        self.command_docs = generate_command_docs(
            self.commands,
            [],
            **self.env_variables,
        )
        if self.format_error_template is None:
            self.format_error_template = self.parse_function.format_error_template
        for command in commands:
            if command.name == self.submit_command:
                self.submit_command_end_name = command.end_name
                break


class SQLToolHandler:
    """
    Handles parsing LLM output and orchestrating the execution of external tool scripts
    """

    def __init__(self, config: SQLToolConfig):
        self.config = config
        self.tool_dir = Path(self.config.tool_dir)
        self.mock_state: dict[str, str] | None = None
        self.logger = get_logger("swea-tools", emoji="🎾")

    def parse_actions(self, output: dict) -> tuple[str, str]:
        return self.config.parse_function(output, self.config.commands)

    def get_state(
        self, env: SQLEnvironmentConfig, timeout: int | float | None = 180
    ) -> dict[str, str]:
        """
        Current attributes in env state:
            - current database name
        """
        if self.mock_state is not None:
            return self.mock_state
        env_state = {
            "database_name": env.database_name,
        }
        self.logger.debug(f"Retrieved state from environment: {env_state}")
        return env_state

    def should_block_action(self, action: str) -> bool:
        return False  # No situation where we'd block anything; modification queries are fair game and may be needed
        # FIXME: potentially block DELETE without WHERE, DROP, TRUNCATE, BEGIN, COMMIT, ROLLBACK

    def execute_action(self, action: str, working_db_path: str) -> str:
        # Handle heredoc markers produced by FunctionCallingParser's invoke_format.
        # When a command has end_name (e.g. execute_sql's ENDOFSQL), the model
        # sometimes also appends the marker in its JSON argument, yielding a
        # double-marker like: execute_sql <<ENDOFSQL\n<sql>\nENDOFSQL\nENDOFSQL
        # We use a regex to reliably strip all heredoc wrapper syntax and extract
        # just the body, regardless of whether multi_line_command_endings is
        # populated (it may be empty if bundles haven't been loaded yet).
        heredoc_match = re.match(
            r"^(\S+)\s+<<(\w+)\n(.*?)\n\2",
            action,
            re.DOTALL,
        )
        if heredoc_match:
            command_name = heredoc_match.group(1)
            heredoc_body = heredoc_match.group(3).strip()
            args = [heredoc_body]
        else:
            try:
                parts = shlex.split(_expand_ansi_c_quotes(action))
                command_name = parts[0]
                args = parts[1:]
            except (ValueError, IndexError):
                return f"Error: Invalid action format. Could not parse command: {action}"
        tool_script_path = self.tool_dir / command_name / "bin" / command_name
        if not tool_script_path.exists():
            return (
                f"Error: Tool script not found for command '{command_name}' at {tool_script_path}"
            )
        # Run tools with the exact interpreter of the current sweagent process.
        # This avoids per-call `uv run` startup overhead while keeping package/env parity.
        base_cmd = [sys.executable, str(tool_script_path)]
        if command_name == "execute_sql":
            full_cmd = base_cmd + [working_db_path] + args
        else:
            full_cmd = base_cmd + args

        try:
            # Build per-subprocess environment to avoid race conditions.
            # Multiple SQL agents run concurrently in the same process, so
            # os.environ["TASK_INSTANCE_ID"] gets overwritten by other threads.
            # Use _task_instance_id (set by agent setup) instead.
            env = os.environ.copy()
            if hasattr(self, "_task_instance_id") and self._task_instance_id:
                env["TASK_INSTANCE_ID"] = self._task_instance_id
                # Resolve per-instance DATABASE_DESCRIPTIONS_DIR so each task
                # reads its own schema CSVs (table_descriptions.csv, <table>.csv).
                # Batch layout: BASE_DIR / <instance_id>/table_descriptions.csv.
                # add-business-info sets TASK_INSTANCE_ID to Mongo attempt_id (no "__") and
                # puts CSVs in a single temp dir; BASE_DIR/attempt_id does not exist — do not
                # overwrite the caller-provided DATABASE_DESCRIPTIONS_DIR in that case.
                base_dir = env.get("DATABASE_DESCRIPTIONS_BASE_DIR")
                if base_dir:
                    original_id = self._task_instance_id.split("__")[0]
                    candidate = Path(base_dir) / original_id
                    table_csv = candidate / "table_descriptions.csv"
                    if candidate.is_dir() and table_csv.is_file():
                        env["DATABASE_DESCRIPTIONS_DIR"] = str(candidate.resolve())
            process = subprocess.run(
                full_cmd,
                capture_output=True,
                text=True,
                check=True,  # raise an exception for non-zero exit codes
                timeout=self.config.execution_timeout,
                env=env,
            )
            return process.stdout
        except subprocess.CalledProcessError as e:
            return f"Error executing tool '{command_name}':\n{e.stderr}"
        except Exception as e:
            return f"An unexpected error occurred while running tool '{command_name}': {e}"
