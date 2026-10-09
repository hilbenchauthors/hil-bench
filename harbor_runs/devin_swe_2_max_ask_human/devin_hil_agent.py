"""Devin adapter additions required by the HiL-Bench ask-human tasks."""

import asyncio
import shlex
from pathlib import Path
from typing import override

from harbor.agents.installed.base import (
    NonZeroAgentExitCodeError,
    with_prompt_template,
)
from harbor.agents.installed.devin import Devin
from harbor.environments.base import BaseEnvironment
from harbor.environments.docker.docker import (
    DockerEnvironment,
    _sanitize_docker_compose_project_name,
)
from harbor.models.agent.context import AgentContext
from harbor.models.trial.paths import EnvironmentPaths


class DevinHiL(Devin):
    """Devin with benchmark-specific ask-human instructions."""

    @staticmethod
    @override
    def name() -> str:
        return "devin-hil"

    async def _install_benchmark_rules(self, environment: BaseEnvironment) -> None:
        rules_path = Path(__file__).with_name("devin-ask-human-instructions.md")
        rules = rules_path.read_text()
        result = await self.exec_as_agent(
            environment,
            command=(
                'CONFIG_DIR="${XDG_CONFIG_HOME:-$HOME/.config}/devin"; '
                'mkdir -p "$CONFIG_DIR"; '
                'echo "$CONFIG_DIR"'
            ),
        )
        await self._upload_config_text(
            environment,
            content=rules,
            remote_path=f"{result.stdout.strip()}/AGENTS.md",
            filename="AGENTS.md",
        )

    @override
    async def install(self, environment: BaseEnvironment) -> None:
        await self.ensure_system_dependencies(environment, ("curl", "bash"))
        await self.exec_as_agent(
            environment,
            command=(
                'CONFIG_DIR="${XDG_CONFIG_HOME:-$HOME/.config}/devin"; '
                'mkdir -p "$CONFIG_DIR"; '
                'echo \'{"shell":{"setup_complete":true}}\' '
                '> "$CONFIG_DIR/config.json"'
            ),
        )
        await self._upload_credentials(environment)
        version_flag = f" {shlex.quote(self._version)}" if self._version else ""
        install_command = (
            'INSTALLER="$(mktemp)"; '
            'FILTERED_INSTALLER="${INSTALLER}.no-setup"; '
            'trap \'rm -f "$INSTALLER" "$FILTERED_INSTALLER"\' EXIT; '
            'curl -fsSL https://cli.devin.ai/install.sh -o "$INSTALLER"; '
            'SETUP_LINE=\'"$VERSION_DIR/bin/$COMPILED_BIN_NAME" setup\'; '
            'grep -Fqx "$SETUP_LINE" "$INSTALLER" || { '
            'echo "Unexpected Devin installer: final setup command not found" >&2; '
            "exit 1; }; "
            'grep -Fvx "$SETUP_LINE" "$INSTALLER" > "$FILTERED_INSTALLER"; '
            f'bash "$FILTERED_INSTALLER"{version_flag}; '
            'export PATH="$HOME/.local/bin:$PATH"; '
            'test -x "$(command -v devin)"'
        )
        if isinstance(environment, DockerEnvironment):
            container_pid = await self._resolve_container_pid(environment)
            process = await asyncio.create_subprocess_exec(
                "sudo",
                "nsenter",
                "-t",
                container_pid,
                "-m",
                "-u",
                "-i",
                "-n",
                "-r",
                "-w",
                "unshare",
                "--mount",
                "--pid",
                "--fork",
                "--mount-proc",
                "bash",
                "-lc",
                install_command,
                stdout=asyncio.subprocess.PIPE,
                stderr=asyncio.subprocess.STDOUT,
            )
            stdout, _ = await process.communicate()
            if process.returncode:
                raise NonZeroAgentExitCodeError(
                    "Host-namespace Devin installer exited "
                    f"{process.returncode}:\n{stdout.decode(errors='replace')}"
                )
        else:
            await self.exec_as_agent(environment, command=install_command)
        if self.mcp_servers:
            await self._write_mcp_config(environment)
        await self._install_benchmark_rules(environment)

    async def _resolve_container_pid(self, environment: DockerEnvironment) -> str:
        project = _sanitize_docker_compose_project_name(environment.session_id)
        lookup = await asyncio.create_subprocess_exec(
            "docker",
            "ps",
            "-q",
            "--filter",
            f"label=com.docker.compose.project={project}",
            "--filter",
            "label=com.docker.compose.service=main",
            stdout=asyncio.subprocess.PIPE,
            stderr=asyncio.subprocess.PIPE,
        )
        lookup_stdout, lookup_stderr = await lookup.communicate()
        container_id = lookup_stdout.decode().strip()
        if lookup.returncode or not container_id:
            raise RuntimeError(
                "Could not resolve the running Harbor main container: "
                f"{lookup_stderr.decode().strip()}"
            )

        inspect = await asyncio.create_subprocess_exec(
            "docker",
            "inspect",
            "-f",
            "{{.State.Pid}}",
            container_id,
            stdout=asyncio.subprocess.PIPE,
            stderr=asyncio.subprocess.PIPE,
        )
        inspect_stdout, inspect_stderr = await inspect.communicate()
        container_pid = inspect_stdout.decode().strip()
        if inspect.returncode or not container_pid.isdigit():
            raise RuntimeError(
                "Could not resolve the Harbor main container PID: "
                f"{inspect_stderr.decode().strip()}"
            )
        return container_pid

    @with_prompt_template
    @override
    async def run(
        self,
        instruction: str,
        environment: BaseEnvironment,
        context: AgentContext,
    ) -> None:
        if not isinstance(environment, DockerEnvironment):
            await super().run(instruction, environment, context)
            return

        agent_dir = EnvironmentPaths.agent_dir.as_posix()
        rollout_log = f"{agent_dir}/rollout.log"
        model = self._execution_model_name()
        model_flag = f"--model {shlex.quote(model)} " if model else ""
        command = (
            "set -o pipefail; "
            'export PATH="$HOME/.local/bin:$PATH"; '
            "export RUST_LOG=debug; "
            f"devin {model_flag}"
            "--permission-mode yolo "
            "--print "
            "--respect-workspace-trust false "
            f"-- {shlex.quote(instruction)} "
            f"2>&1 | tee {rollout_log}"
        )

        await self.exec_as_agent(environment, command=f"mkdir -p {agent_dir}")
        container_pid = await self._resolve_container_pid(environment)

        process = await asyncio.create_subprocess_exec(
            "sudo",
            "nsenter",
            "-t",
            container_pid,
            "-m",
            "-u",
            "-i",
            "-n",
            "-r",
            "-w",
            "unshare",
            "--mount",
            "--pid",
            "--fork",
            "--mount-proc",
            "bash",
            "-lc",
            command,
            stdout=asyncio.subprocess.PIPE,
            stderr=asyncio.subprocess.STDOUT,
        )
        try:
            stdout, _ = await process.communicate()
        except asyncio.CancelledError:
            process.kill()
            await process.wait()
            raise
        finally:
            await self.exec_as_agent(
                environment,
                command=(
                    f'DB="${{XDG_DATA_HOME:-$HOME/.local/share}}/devin/cli/sessions.db"; '
                    f"if command -v sqlite3 >/dev/null; then "
                    f'sqlite3 "$DB" ".backup {agent_dir}/sessions.db"; '
                    f'else cp "$DB" "$DB-wal" "$DB-shm" {agent_dir}/ 2>/dev/null; fi '
                    f"|| true"
                ),
            )

        if process.returncode:
            output = stdout.decode(errors="replace")
            raise NonZeroAgentExitCodeError(
                f"Host-namespace Devin exited {process.returncode}:\n{output}"
            )
