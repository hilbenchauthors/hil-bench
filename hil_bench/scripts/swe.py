import json
import os
import shutil
import subprocess
import sys
import tempfile
from contextlib import ExitStack
from pathlib import Path
from typing import Any

import yaml
from jinja2 import Environment, FileSystemLoader, StrictUndefined

from ..utils.server_utils import (
    AskHumanServerError,
    BusinessInfoServerError,
    start_ask_human_server,
    start_business_info_server,
)
from ..utils.set_task_env import add_task_env_to_instances

REQUIRE_BUFFED_CHROMA_ENV = "HIL_BENCH_REQUIRE_BUFFED_CHROMA"
_RUN_OWNER_DIR = Path("/tmp/hil_bench_run_owners")


def _any_hil_bench_run_active() -> bool:
    """Return True if any registered run_hil_bench.py process is still alive.

    run_hil_bench.py writes a {pid}.owner token into _RUN_OWNER_DIR on startup
    and removes it on exit.  If any such token maps to a live PID, at least one
    orchestrating process is active and its Docker containers must not be touched.
    Stale tokens (dead PIDs) are cleaned up here so they don't accumulate.
    """
    if not _RUN_OWNER_DIR.exists():
        return False
    for token in _RUN_OWNER_DIR.glob("*.owner"):
        try:
            pid = int(token.stem)
            os.kill(pid, 0)
            return True
        except ProcessLookupError:
            token.unlink(missing_ok=True)
        except (ValueError, PermissionError):
            return True
    return False


def _resolve_relative_path(path_value: str, project_root: Path) -> str:
    """Resolve non-absolute paths against known repository roots."""
    if not path_value:
        return path_value
    path = Path(path_value)
    if path.is_absolute():
        return str(path)

    # Prefer repo root first; many paths are "research_evals/hil_bench/..."
    repo_root = project_root.parent.parent
    candidate_roots = [repo_root, project_root.parent, project_root]
    for root in candidate_roots:
        candidate = (root / path).resolve()
        if candidate.exists():
            return str(candidate)

    # Deterministic fallback even when file doesn't exist yet.
    return str((repo_root / path).resolve())


def _normalize_and_validate_sql_instances(
    original_instances: list[dict[str, Any]], project_root: Path
) -> None:
    """Normalize SQL paths and validate DB state expectations."""
    for inst in original_instances:
        env = inst.get("env", {})
        if not isinstance(env, dict):
            continue

        for path_key in ["base_db_path", "working_db_path"]:
            p = env.get(path_key, "")
            if p:
                env[path_key] = _resolve_relative_path(p, project_root)
        chroma_runtime_path = env.get("chroma_path", "")
        if chroma_runtime_path:
            env["chroma_path"] = _resolve_relative_path(chroma_runtime_path, project_root)
            if not Path(env["chroma_path"]).exists():
                raise FileNotFoundError(
                    f"SQL instance has missing env.chroma_path: {env['chroma_path']!r}"
                )

        ps = inst.get("problem_statement", {})
        if isinstance(ps, dict):
            for path_key in ["blocker_registry_path", "table_descriptions_path"]:
                p = ps.get(path_key, "")
                if p:
                    ps[path_key] = _resolve_relative_path(p, project_root)

        base_db_path = env.get("base_db_path", "")
        if not base_db_path or not Path(base_db_path).exists():
            raise FileNotFoundError(
                f"SQL instance has missing base_db_path: {base_db_path!r}. "
                "Refusing to run with an unknown database path."
            )

        # At this stage (instances.json for runtime), diff queries must already be
        # applied and serialized as an empty list in env.diff_queries.
        diff_queries = env.get("diff_queries", [])
        if diff_queries is None:
            diff_queries = []
        if not isinstance(diff_queries, list):
            raise TypeError(
                "SQL instance env.diff_queries must be a list at runtime "
                f"(got {type(diff_queries).__name__})."
            )
        if diff_queries:
            raise ValueError(
                "SQL instance still has non-empty diff_queries at runtime. "
                "Refusing to run because database diffs must be pre-applied."
            )


def cleanup_stale_docker_containers():
    """
    Clean up stale Docker containers from previous SWE-agent runs.
    """
    print("🧹 Cleaning up stale Docker containers...")

    # Check if docker is available
    try:
        subprocess.run(
            ["docker", "--version"],
            stdout=subprocess.DEVNULL,
            stderr=subprocess.DEVNULL,
            check=True,
        )
    except (subprocess.CalledProcessError, FileNotFoundError):
        print("⚠️  Warning: Docker not available, skipping cleanup", file=sys.stderr)
        return

    try:
        name_filters = [
            "sweagentswe-agentlatest",
            "hil-bench-agent",
            "sweb",
            "rex-deploy",
            "validation-",
        ]
        for name_filter in name_filters:
            for status in ["created", "exited"]:
                result = subprocess.run(
                    [
                        "docker",
                        "ps",
                        "-aq",
                        "--filter",
                        f"status={status}",
                        "--filter",
                        f"name={name_filter}",
                    ],
                    capture_output=True,
                    text=True,
                    check=False,
                )
                container_ids = [
                    cid.strip() for cid in result.stdout.strip().split("\n") if cid.strip()
                ]
                if container_ids:
                    subprocess.run(
                        ["docker", "rm", "-f"] + container_ids,
                        stdout=subprocess.DEVNULL,
                        stderr=subprocess.DEVNULL,
                        check=False,
                    )
                    print(
                        f"   Removed {len(container_ids)} {status} containers (filter: {name_filter})"
                    )

        # Clean up containers by image pattern OR name pattern
        # This catches containers whose image shows as ID instead of name
        image_patterns = [
            "hil-bench-agent:",
            "jefzda/sweap-images:",
            "sweb.eval.",
            "local/sweb.eval.",
        ]
        name_patterns = ["hil-bench-agent", "sweagent", "sweb", "rex-deploy", "validation-"]

        result = subprocess.run(
            [
                "docker",
                "ps",
                "-a",
                "--format",
                "{{.ID}}\t{{.Image}}\t{{.Names}}\t{{.Status}}\t{{.RunningFor}}",
            ],
            capture_output=True,
            text=True,
            check=False,
        )
        active_owner_exists = _any_hil_bench_run_active()
        containers_to_remove = []
        for line in result.stdout.strip().split("\n"):
            if not line.strip():
                continue
            parts = line.split("\t")
            if len(parts) >= 5:
                container_id, image, name, status = (
                    parts[0],
                    parts[1],
                    parts[2],
                    parts[3].lower(),
                )
                is_exited = status.startswith("created") or status.startswith("exited")
                is_running = status.startswith("up")
                if is_exited:
                    removable = True
                elif is_running:
                    removable = not active_owner_exists
                else:
                    removable = False
                if not removable:
                    continue
                if any(pattern in image for pattern in image_patterns):
                    containers_to_remove.append(container_id)
                elif any(pattern in name for pattern in name_patterns):
                    containers_to_remove.append(container_id)

        if containers_to_remove:
            subprocess.run(
                ["docker", "rm", "-f"] + containers_to_remove,
                stdout=subprocess.DEVNULL,
                stderr=subprocess.DEVNULL,
                check=False,
            )
            print(f"   Removed {len(containers_to_remove)} containers by image/name pattern")

    except Exception as e:
        print(f"⚠️  Warning: Docker cleanup failed: {e}", file=sys.stderr)


def cleanup_old_trajectories(trajectory_dir: Path):
    """
    Clean up old trajectory data from previous runs.
    Matches the cleanup logic from run.sh.

    Args:
        trajectory_dir: Path to trajectory directory
    """
    print("🧹 Clearing old trajectories...")

    if not trajectory_dir.exists():
        return

    # Remove old files
    for filename in [
        "preds.json",
        "run_batch_exit_statuses.yaml",
        "run_batch.log",
        "run_batch.config.yaml",
    ]:
        file_path = trajectory_dir / filename
        if file_path.exists():
            file_path.unlink()

    # Remove old trajectory directories (pattern: *__*)
    for traj_dir in trajectory_dir.iterdir():
        if traj_dir.is_dir() and "__" in traj_dir.name:
            shutil.rmtree(traj_dir, ignore_errors=True)


def get_task_dir_for_instance(instance: dict, task_folder: Path) -> Path | None:
    """
    Find the task directory for an instance.

    The task directory contains blocker_registry.json and other task files.
    It can be found by:
    1. Looking at repo_name - if it's a local path, the task dir is its parent
    2. Falling back to instance_id (legacy behavior)

    Args:
        instance: Instance dict with instance_id and optionally repo_name
        task_folder: Parent folder containing task subdirectories

    Returns:
        Path to task directory, or None if not found
    """
    # Single-task mode: caller may pass the task directory itself (which contains blocker_registry.json).
    # In that case we should treat task_folder as the task_dir directly.
    if (task_folder / "blocker_registry.json").exists():
        return task_folder

    instance_id = instance["instance_id"]

    # Try to find task dir from repo_name (most reliable for local repos)
    repo_name = instance.get("repo_name", "")
    if repo_name and not repo_name.startswith("http"):
        # Local repo path - task dir is parent of repo
        repo_path = Path(repo_name)
        if repo_path.exists():
            task_dir = repo_path.parent
            if task_dir.exists():
                return task_dir

    # Try using instance_id directly as folder name
    task_dir = task_folder / instance_id
    if task_dir.exists():
        return task_dir

    # Try extracting folder name from instance_id (format: folder__something)
    # This handles cases like "demo__simple_demo" where folder is "demo"
    if "__" in instance_id:
        folder_name = instance_id.split("__")[0]
        task_dir = task_folder / folder_name
        if task_dir.exists():
            return task_dir

    return None


def validate_blocker_registries(
    task_folder: Path, instances_file: Path, num_tasks: int | None = None
):
    """
    Validate that all tasks have blocker_registry.json files.

    Args:
        task_folder: Path to parent folder containing task subdirectories, or task folder itself (single mode)
        instances_file: Path to instances.json file
        num_tasks: Optional limit on number of tasks to validate

    Raises:
        FileNotFoundError: If any task is missing blocker_registry.json
    """
    if not task_folder.exists():
        return

    # Load instances to get task IDs
    with open(instances_file, "r") as f:
        instances = json.load(f)

    # Limit to num_tasks if specified
    if num_tasks is not None:
        instances = instances[:num_tasks]

    missing = []

    # Single task mode: blocker_registry.json is directly in task_folder
    if len(instances) == 1 and (task_folder / "blocker_registry.json").exists():
        return

    for instance in instances:
        instance_id = instance["instance_id"]
        task_dir = get_task_dir_for_instance(instance, task_folder)

        if task_dir is None:
            missing.append(instance_id)
            print(f"⚠️  Missing task dir for: {instance_id}")
            continue

        blocker_registry = task_dir / "blocker_registry.json"

        if not blocker_registry.exists():
            missing.append(instance_id)
            print(f"⚠️  Missing: {blocker_registry}")

    if missing:
        raise FileNotFoundError(
            f"{len(missing)} tasks missing blocker_registry.json: {', '.join(missing[:5])}"
            + (f" and {len(missing) - 5} more" if len(missing) > 5 else "")
        )


def resolve_swe_input_path(
    path: Path, max_tasks: int | None = None
) -> tuple[str, Path, Path, Path | None]:
    """
    Resolve CLI input into a runnable form for SWE.

    Valid inputs:
    - instances file (JSON): treated as batch mode
    - directory:
        - if the directory contains problem_statement.txt (single task), use it directly
        - otherwise, treat it as a "tasks directory" and use all direct subdirectories
          that contain problem_statement.txt. In this case we create a temporary
          instances.json in /tmp and return it.

    Returns:
        (input_type, resolved_path, task_folder, temp_instances_file)
        - input_type: 'batch' or 'single'
        - resolved_path: instances.json path for batch, or task folder path for single
        - task_folder: directory to use for blocker registry lookup/augmentation
        - temp_instances_file: temp instances file path if created, else None
    """
    # Batch: direct instances file
    if path.is_file() and path.suffix == ".json":
        return ("batch", path, path.parent, None)

    if not path.is_dir():
        raise FileNotFoundError(
            f"Invalid input: {path}. Expected either an instances.json file or a directory."
        )

    # Single task: directory contains problem_statement.txt (or metadata.json fallback)
    if (path / "problem_statement.txt").exists() or (path / "metadata.json").exists():
        return ("single", path, path, None)

    # Tasks directory: use direct subdirectories with problem_statement.txt
    task_dirs = [
        d
        for d in path.iterdir()
        if d.is_dir() and not d.name.startswith(".") and (d / "problem_statement.txt").exists()
    ]
    if not task_dirs:
        raise FileNotFoundError(
            f"Could not find any direct subdirectories with problem_statement.txt under {path}.\n"
            f"Expected either:\n"
            f"  - {path}/problem_statement.txt (single task)\n"
            f"  - {path}/*/problem_statement.txt (tasks directory)"
        )

    # sort for deterministic instance ordering
    task_dirs = sorted(task_dirs, key=lambda p: p.name)
    if max_tasks is not None:
        task_dirs = task_dirs[:max_tasks]

    instances: list[dict] = [create_single_instance_file(d, full_info=False) for d in task_dirs]

    tmp = tempfile.NamedTemporaryFile(
        mode="w", suffix=".json", delete=False, dir="/tmp", prefix="hil_bench_instances_"
    )
    tmp.write(json.dumps(instances, indent=2))
    tmp.close()
    tmp_path = Path(tmp.name)

    return ("batch", tmp_path, path, tmp_path)


def detect_input_type(path: Path) -> tuple[str, Path]:
    """
    Detect whether the path is an instances.json file (batch) or a task folder (single).

    Returns:
        tuple: (type, path) where type is 'batch' or 'single'
    """
    input_type, resolved_path, _task_folder, _tmp = resolve_swe_input_path(path)
    return (input_type, resolved_path)


def augment_problem_full_info(problem_statement: str, task_folder: Path) -> str:
    """
    Augment problem statement with blocker information from blocker_registry.json.

    Args:
        problem_statement: Original problem statement
        task_folder: Path to task folder containing blocker_registry.json

    Returns:
        Augmented problem statement with blocker info, or original if no blockers
    """
    blocker_registry_path = task_folder / "blocker_registry.json"
    if not blocker_registry_path.exists():
        return problem_statement

    with open(blocker_registry_path, "r") as f:
        blockers_data = json.load(f)

    if not blockers_data:
        return problem_statement

    # Expected format: {"blockers": [{"id": ..., "description": ..., "resolution": ...}, ...]}
    if not isinstance(blockers_data, dict) or "blockers" not in blockers_data:
        raise ValueError(
            f"Invalid blocker registry format in {blocker_registry_path}. "
            "Expected dict with 'blockers' key containing a list."
        )

    local_dir = Path(__file__).parent
    template_env = Environment(
        loader=FileSystemLoader(local_dir.parent / "templates"), undefined=StrictUndefined
    )
    template = template_env.get_template("problem_full_info.jinja2")

    augmented = template.render(
        problem_statement=problem_statement,
        blockers=blockers_data["blockers"],
    )

    return augmented


def augment_problem_full_info_from_path(
    problem_statement: str, blocker_registry_path: Path
) -> str:
    """
    Augment problem statement with blocker information from a specific registry file.

    Args:
        problem_statement: Original problem statement
        blocker_registry_path: Path to blocker_registry.json file

    Returns:
        Augmented problem statement with blocker info, or original if no blockers
    """
    if not blocker_registry_path.exists():
        return problem_statement

    with open(blocker_registry_path, "r") as f:
        blockers_data = json.load(f)

    if not blockers_data:
        return problem_statement

    # Expected format: {"blockers": [{"id": ..., "description": ..., "resolution": ...}, ...]}
    if not isinstance(blockers_data, dict) or "blockers" not in blockers_data:
        raise ValueError(
            f"Invalid blocker registry format in {blocker_registry_path}. "
            "Expected dict with 'blockers' key containing a list."
        )

    local_dir = Path(__file__).parent
    template_env = Environment(
        loader=FileSystemLoader(local_dir.parent / "templates"), undefined=StrictUndefined
    )
    template = template_env.get_template("problem_full_info.jinja2")

    augmented = template.render(
        problem_statement=problem_statement,
        blockers=blockers_data["blockers"],
    )

    return augmented


def create_single_instance_file(task_folder: Path, full_info: bool = False) -> dict:
    """
    Create an instance dict for a single task folder.

    Args:
        task_folder: Path to task folder
        full_info: If True, augment problem statement with blocker info
    """
    from ..utils.instance_utils import load_instance_from_task_dir

    return load_instance_from_task_dir(
        task_dir=task_folder,
        augment_blockers_fn=augment_problem_full_info if full_info else None,
    )


def load_agent_config_from_yaml(config_path: str | Path) -> dict[str, Any]:
    """
    Load agent config from a YAML file.

    Args:
        config_path: Path to the YAML config file

    Returns:
        The agent config dict from the YAML file
    """
    with open(config_path, "r") as f:
        config = yaml.safe_load(f)

    def expand_env_values(value: Any) -> Any:
        if isinstance(value, str):
            return os.path.expandvars(value)
        if isinstance(value, list):
            return [expand_env_values(v) for v in value]
        if isinstance(value, dict):
            return {k: expand_env_values(v) for k, v in value.items()}
        return value

    config = expand_env_values(config)
    agent_config = config.get("agent", config)
    hosting = config.get("hosting", {})
    if isinstance(agent_config, dict):
        model = agent_config.get("model", {})
        if isinstance(model, dict):
            has_api_base = bool(str(model.get("api_base") or "").strip())
            api_base_env = hosting.get("api_base_env") if isinstance(hosting, dict) else None
            hosting_type = str(hosting.get("type") or "").strip() if isinstance(hosting, dict) else ""
            if (
                hosting_type == "self_hosted"
                and not has_api_base
                and api_base_env is not None
                and str(api_base_env).strip()
            ):
                env_name = str(api_base_env).strip()
                api_base = os.getenv(env_name, "").strip()
                if not api_base:
                    raise ValueError(
                        f"Agent config expects env var '{env_name}' for hosting.api_base_env "
                        f"but it is not set ({config_path})"
                    )
                model["api_base"] = api_base
                agent_config["model"] = model
            has_api_key = bool(str(model.get("api_key") or "").strip())
            if hosting_type == "litellm_proxy" and not has_api_key:
                model["api_key"] = "$LITELLM_API_KEY"
                agent_config["model"] = model
    return agent_config


def create_mixed_mode_instances(
    instances: list[dict],
    model_configs: list[
        tuple[str, str, bool, bool]
    ],  # (model_name, mode_name, enable_ask, full_info)
    resolved_agent_configs: dict[tuple[str, str], str],
    task_folder: Path,
    project_root: Path,
    per_instance_cost_limit: float = 5.0,
    max_steps: int | None = None,
    enable_model_call_logging: bool = False,
    passes: int = 1,
    task_type: str = "swe",
) -> list[dict]:
    """
    Create expanded instances for mixed model/mode runs.

    Each instance is duplicated for each model/mode combination, with the appropriate
    config and problem statement modifications applied.

    Args:
        instances: Original instances list
        model_configs: List of (model_name, mode_name, enable_ask, full_info) tuples
        resolved_agent_configs: Mapping of (model_name, mode_name) to full config path
        task_folder: Path to task folder for blocker augmentation
        project_root: Project root for config paths
        per_instance_cost_limit: Cost limit per instance
        max_steps: Maximum steps before auto-submit (None = use config file default)
        enable_model_call_logging: Enable verbose model call logging for Datadog
        passes: Number of passes to run for each configuration
        task_type: "swe" or "sql" - determines config files and instance format

    Returns:
        Expanded instances with per-instance model/mode configuration
    """
    expanded = []

    for model_name, mode_name, enable_ask, full_info in model_configs:
        config_path = resolved_agent_configs[(model_name, mode_name)]
        base_config = load_agent_config_from_yaml(config_path)

        # Override model settings
        if "model" not in base_config:
            base_config["model"] = {}
        base_config["model"]["name"] = model_name

        # If the model does not support function calling, switch parser to thought_action.
        # Otherwise the agent can get stuck in repeated format requery loops.
        try:
            import litellm

            parse_cfg = base_config.get("tools", {}).get("parse_function", {})
            uses_function_calling = (
                isinstance(parse_cfg, dict) and parse_cfg.get("type") == "function_calling"
            )
            force_thought_action_models = {"openai/gpt-5.2-pro"}
            should_disable_fcalling = model_name in force_thought_action_models
            has_custom_api_base = "api_base" in base_config.get("model", {})
            if uses_function_calling and not should_disable_fcalling and not has_custom_api_base:
                should_disable_fcalling = not litellm.utils.supports_function_calling(
                    model=model_name
                )
            if uses_function_calling and should_disable_fcalling:
                base_config.setdefault("tools", {})
                base_config["tools"]["parse_function"] = {"type": "thought_action"}
                base_config["tools"]["enable_bash_tool"] = True
                print(
                    f"⚠️  {model_name} does not support function calling; "
                    "using parse_function=thought_action to avoid format-loop stalls"
                )
        except Exception:
            pass

        # Check if model is in litellm.model_cost; if not, disable cost limit
        # to avoid ModelConfigurationError (e.g., openai/gemini-3-pro-preview)
        effective_cost_limit = per_instance_cost_limit
        try:
            import litellm

            # Only check the exact model name as it will be used at runtime.
            if model_name not in litellm.model_cost:
                effective_cost_limit = 0
                # Check for a model registry file to register the model
                registry_file = (
                    project_root / "configs" / f"litellm_{model_safe_name}_registry.json"
                )
                if not registry_file.exists():
                    # Try a simpler name pattern
                    for f in project_root.glob("configs/litellm_*registry.json"):
                        import json as _json

                        with open(f) as _f:
                            reg = _json.load(_f)
                        if model_name in reg:
                            registry_file = f
                            break
                if registry_file.exists():
                    base_config["model"]["litellm_model_registry"] = str(registry_file)
        except Exception:
            pass
        base_config["model"]["per_instance_cost_limit"] = effective_cost_limit
        base_config["model"]["total_cost_limit"] = 0

        # Override max_steps at agent level
        if max_steps is not None:
            base_config["max_steps"] = max_steps

        # Some endpoints are frequently unhealthy/slow and can hold the whole batch
        # hostage via long retry backoff. Keep retries/timeouts bounded for them.
        bounded_retry_models = {
            "openai/gpt-5.2-pro",
            "gemini/gemini-3.1-pro-preview",
        }
        if model_name in bounded_retry_models:
            retry_cfg = base_config["model"].get("retry", {})
            if not isinstance(retry_cfg, dict):
                retry_cfg = {}
            retry_cfg["retries"] = min(int(retry_cfg.get("retries", 20)), 6)
            retry_cfg["min_wait"] = min(float(retry_cfg.get("min_wait", 10)), 3.0)
            retry_cfg["max_wait"] = min(float(retry_cfg.get("max_wait", 120)), 20.0)
            base_config["model"]["retry"] = retry_cfg

            completion_kwargs = base_config["model"].get("completion_kwargs", {})
            if not isinstance(completion_kwargs, dict):
                completion_kwargs = {}
            completion_kwargs["timeout"] = min(int(completion_kwargs.get("timeout", 300)), 120)
            base_config["model"]["completion_kwargs"] = completion_kwargs

        # Enable model call logging if requested (for Datadog visibility)
        if enable_model_call_logging:
            base_config["model"]["enable_model_call_logging"] = True

        for pass_num in range(1, passes + 1):
            for instance in instances:
                new_instance = instance.copy()
                # Handle both SWE format (instance_id) and SQL format (problem_statement.id)
                if "instance_id" in instance:
                    original_id = instance["instance_id"]
                elif "problem_statement" in instance and isinstance(
                    instance["problem_statement"], dict
                ):
                    original_id = instance["problem_statement"].get("id", "unknown")
                else:
                    original_id = "unknown"

                # Create unique ID for this model/mode/pass combination
                mode_safe = mode_name.replace("-", "_")
                model_safe = model_name.replace("/", "_").replace(":", "_")
                if passes > 1:
                    new_id = f"{original_id}__{model_safe}__{mode_safe}__pass_{pass_num}"
                else:
                    new_id = f"{original_id}__{model_safe}__{mode_safe}"

                new_instance["instance_id"] = new_id

                # For SQL instances (expert_file), also update problem_statement.id
                # since that's what sweagent uses for directory names
                if "problem_statement" in new_instance and isinstance(
                    new_instance["problem_statement"], dict
                ):
                    new_instance["problem_statement"] = new_instance["problem_statement"].copy()
                    new_instance["problem_statement"]["id"] = new_id

                # Store metadata for later reorganization
                new_instance["_original_instance_id"] = original_id
                new_instance["_model_name"] = model_name
                new_instance["_mode_name"] = mode_name
                new_instance["_pass_number"] = pass_num

                # Set per-instance overrides in extra_fields
                # For SQL instances, extra_fields must be inside problem_statement
                # because sweagent reads from instance.problem_statement.extra_fields
                # For SWE instances, extra_fields is at the top level of the instance
                extra = {"_model_name": model_name, "_agent_config": base_config}

                if task_type == "sql":
                    # SQL: Store extra_fields inside problem_statement
                    ps = new_instance["problem_statement"]
                    if isinstance(ps, dict):
                        ps_extra = ps.get("extra_fields", {})
                        ps_extra.update(extra)
                        ps["extra_fields"] = ps_extra
                else:
                    # SWE: Store extra_fields at top level
                    top_extra = new_instance.get("extra_fields", {})
                    top_extra.update(extra)
                    new_instance["extra_fields"] = top_extra

                # Handle full_info mode: augment problem statement
                if full_info:
                    if task_type == "sql":
                        # SQL: each instance has blocker_registry_path in problem_statement
                        ps = new_instance.get("problem_statement", {})
                        if isinstance(ps, dict):
                            registry_path_str = ps.get("blocker_registry_path")
                            if registry_path_str:
                                registry_path = Path(registry_path_str)
                                original_question = ps.get("question", "")
                                augmented_question = augment_problem_full_info_from_path(
                                    original_question, registry_path
                                )
                                new_instance["problem_statement"]["question"] = augmented_question
                    else:
                        # SWE: per-task blocker registries in task directories
                        task_dir = get_task_dir_for_instance(instance, task_folder)
                        if task_dir and task_dir.exists():
                            original_problem = new_instance.get("problem_statement", "")
                            new_instance["problem_statement"] = augment_problem_full_info(
                                original_problem, task_dir
                            )

                # For ask_human mode, add TASK_INSTANCE_ID to extra_fields
                # Use the full expanded instance ID (with model/mode/pass) so logs are per-pass
                # The server's get_registry_path_for_instance() will strip suffixes to find the registry
                if enable_ask:
                    if task_type == "sql":
                        ps = new_instance["problem_statement"]
                        if isinstance(ps, dict):
                            ps["extra_fields"]["TASK_INSTANCE_ID"] = new_instance["instance_id"]
                    else:
                        if "extra_fields" not in new_instance:
                            new_instance["extra_fields"] = {}
                        new_instance["extra_fields"]["TASK_INSTANCE_ID"] = new_instance[
                            "instance_id"
                        ]

                expanded.append(new_instance)

    return expanded


def run_sweagent_batch(
    instances_file: Path,
    model_configs: list[
        tuple[str, str, bool, bool]
    ],  # (model_name, mode_name, enable_ask, full_info)
    output_dir: Path,
    task_folder: Path,
    num_workers: int = 5,
    num_tasks: int | None = None,
    per_instance_cost_limit: float = 5.0,
    max_steps: int | None = None,
    enable_model_call_logging: bool = False,
    redo_existing: bool = True,
    cleanup_docker: bool = True,
    cleanup_trajectories: bool = False,
    dataset_name: str = "princeton-nlp/SWE-bench_Verified",
    passes: int = 1,
    resolved_agent_configs: dict[tuple[str, str], str] | None = None,
    judge_config: Path | None = None,
    task_type: str = "swe",
    instances_type: str = "file",
    **kwargs,
) -> tuple[int, dict | None]:
    """
    Run SWE-agent batch mode with mixed models and modes in a single call.

    This is more efficient than running separate batches for each model/mode
    because it only starts the ask_human server once (if needed) and runs
    all instances in parallel.

    Args:
        instances_file: Path to instances.json file
        model_configs: List of (model_name, mode_name, enable_ask, full_info) tuples
        output_dir: Output directory
        task_folder: Parent folder containing task subdirectories
        num_workers: Number of parallel workers
        num_tasks: Limit number of tasks (applied to original instances)
        per_instance_cost_limit: Cost limit per task
        max_steps: Maximum agent steps before auto-submit (None = use config default)
        redo_existing: Re-run existing results
        cleanup_docker: Clean up stale Docker containers before running
        cleanup_trajectories: Clean up old trajectory data before running
        dataset_name: SWE-bench dataset name for pass@1 evaluation
        passes: Number of passes to run for each model/mode combination
        resolved_agent_configs: Required mapping of (model_name, mode_name) to config YAML paths
        judge_config: Optional ask_human judge config YAML path
        task_type: "swe" or "sql" - determines config files and instance handling
        instances_type: "file" for SWE, "expert_file" for SQL
        **kwargs: Additional arguments

    Returns:
        Tuple of (return_code, ask_human_logs):
        - return_code: 0 for success, non-zero for failure
        - ask_human_logs: Dict of instance_id -> log entries (if ask_human was used), else None
    """
    local_dir = Path(__file__).parent
    project_root = local_dir.parent.parent

    # Load original instances
    with open(instances_file, "r") as f:
        original_instances = json.load(f)

    # For SQL instances, resolve relative paths and enforce DB invariants.
    if task_type == "sql":
        _normalize_and_validate_sql_instances(original_instances, project_root)

    # Limit instances if requested
    if num_tasks:
        original_instances = original_instances[:num_tasks]

    # Check if any mode needs ask_human
    needs_ask_human = any(enable_ask for _, _, enable_ask, _ in model_configs)

    # Validate blocker registries if any mode uses ask_human
    # For SQL, also build a blockers dict to pass to the server (keyed by instance_id)
    sql_blockers_dict = None
    if needs_ask_human:
        if task_type == "sql":
            # SQL: each instance has blocker_registry_path in problem_statement
            # Build blockers dict; the path may be relative to various base dirs, so try multiple
            sql_blockers_dict = {}
            for instance in original_instances:
                ps = instance.get("problem_statement", {})
                if isinstance(ps, dict):
                    registry_path_str = ps.get("blocker_registry_path")
                    instance_id = ps.get("id")  # Get the actual instance_id
                    if registry_path_str:
                        registry_path = Path(registry_path_str)
                        actual_path = None
                        if registry_path.exists():
                            actual_path = registry_path
                        else:
                            # Try relative to project root and ancestors
                            base = project_root
                            for _ in range(5):  # walk up to 5 levels
                                if (base / registry_path_str).exists():
                                    actual_path = base / registry_path_str
                                    break
                                base = base.parent
                        if actual_path is None:
                            print(
                                f"⚠️  Blocker registry not found: {registry_path} (non-fatal, continuing)",
                                file=sys.stderr,
                            )
                            # Don't abort -- the ask_human server will handle missing registries
                        elif instance_id:
                            # Load the blocker registry and map by instance_id
                            try:
                                with open(actual_path, "r") as f:
                                    sql_blockers_dict[instance_id] = json.load(f)
                            except Exception as e:
                                print(
                                    f"⚠️  Failed to load blocker registry {actual_path}: {e} (non-fatal)",
                                    file=sys.stderr,
                                )
        else:
            # SWE: per-task blocker registries in task directories
            validate_blocker_registries(task_folder, instances_file, num_tasks)

    if not resolved_agent_configs:
        raise ValueError("resolved_agent_configs is required and cannot be empty")

    # Create expanded instances with per-instance configs
    expanded_instances = create_mixed_mode_instances(
        instances=original_instances,
        model_configs=model_configs,
        resolved_agent_configs=resolved_agent_configs,
        task_folder=task_folder,
        project_root=project_root,
        per_instance_cost_limit=per_instance_cost_limit,
        max_steps=max_steps,
        enable_model_call_logging=enable_model_call_logging,
        passes=passes,
        task_type=task_type,
    )

    # Write expanded instances to temp file
    output_dir.mkdir(parents=True, exist_ok=True)
    temp_file = tempfile.NamedTemporaryFile(mode="w", suffix=".json", delete=False, dir=output_dir)
    json.dump(expanded_instances, temp_file, indent=2)
    temp_file.close()
    expanded_instances_path = Path(temp_file.name)

    # Add TASK_INSTANCE_ID to instances for ask_human mode
    if needs_ask_human:
        add_task_env_to_instances(str(expanded_instances_path))

    # Cleanup operations
    if cleanup_docker:
        cleanup_stale_docker_containers()

    if cleanup_trajectories:
        cleanup_old_trajectories(output_dir)

    first_model = model_configs[0][0] if model_configs else "unknown"
    first_mode = model_configs[0][1] if model_configs else "baseline"
    config = resolved_agent_configs[(first_model, first_mode)]

    # Check if any model is not in litellm.model_cost; if so, disable global cost limit
    # and rely on per-instance _agent_config cost limits instead
    global_cost_limit = per_instance_cost_limit
    try:
        import litellm

        for model_name_check, _, _, _ in model_configs:
            if model_name_check not in litellm.model_cost:
                global_cost_limit = 0
                print(
                    f"⚠️  {model_name_check} not in litellm.model_cost; "
                    f"disabling global cost limit (per-instance limits still apply)"
                )
                break
    except Exception:
        pass

    # Pre-build Docker images for non-Python tasks to avoid parallel build races.
    # When multiple workers try to build the same image simultaneously, they can
    # fail due to resource contention. Building once here warms the Docker cache.
    # The image info is in task metadata files, not in the expanded instance configs.
    try:
        seen_images = set()
        for metadata_file in task_folder.glob("*/metadata.json"):
            with open(metadata_file) as _mf:
                meta = json.load(_mf)
            image = meta.get("image_name", meta.get("base_image", ""))
            if image and "python" not in image.lower() and image not in seen_images:
                seen_images.add(image)
                print(f"🔨 Pre-building Docker image for non-Python base: {image}")
                try:
                    # IMPORTANT: sweagent applies monkey-patches to swerex Dockerfile generation
                    # at import-time (in sweagent.__init__). We must import sweagent here so this
                    # pre-build uses the exact same Dockerfile recipe as the later `sweagent run-batch`
                    # process; otherwise cache warming may target a different image recipe.
                    import sweagent  # noqa: F401
                    from swerex.deployment.config import DockerDeploymentConfig
                    from swerex.deployment.docker import DockerDeployment

                    cfg = DockerDeploymentConfig(image=image, python_standalone_dir="/root")
                    dep = DockerDeployment.from_config(cfg)
                    dockerfile = dep.glibc_dockerfile
                    import subprocess as _sp

                    prebuild_ok = False
                    for attempt in range(1, 4):
                        result = _sp.run(
                            ["docker", "build", "-q", "--build-arg", f"BASE_IMAGE={image}", "-"],
                            input=dockerfile.encode(),
                            capture_output=True,
                            timeout=1800,
                        )
                        if result.returncode == 0:
                            prebuild_ok = True
                            print(f"   ✅ Docker image pre-built for {image} (attempt {attempt})")
                            break
                        err_tail = result.stderr.decode(errors="replace")[-1200:]
                        print(
                            f"   ⚠️  Docker pre-build attempt {attempt} failed for {image}: {err_tail}"
                        )
                    if not prebuild_ok:
                        print(
                            f"   ❌ Docker pre-build failed for {image} after 3 attempts. "
                            "Subsequent task runs may fail during environment startup."
                        )
                except Exception as e:
                    print(f"   ⚠️  Docker pre-build skipped for {image}: {e}")
    except Exception:
        pass

    # Resolve output_dir to absolute so it stays valid when cwd changes
    output_dir = Path(output_dir).resolve()

    kwargs = dict(kwargs)
    cmd = [
        sys.executable,
        "-m",
        "sweagent",
        "run-batch",
        f"--agent.model.name={first_model}",  # Will be overridden per-instance
        f"--agent.model.per_instance_cost_limit={global_cost_limit}",
        "--agent.model.total_cost_limit=0",  # Disable global total cost limit; per-instance handles it
        f"--instances.type={instances_type}",
        f"--instances.path={expanded_instances_path}",
        "--instances.shuffle=False",
        f"--num_workers={num_workers}",
        f"--redo_existing={redo_existing}",
        f"--config={config}",
        f"--output_dir={output_dir}",
    ]

    # Add any additional kwargs as CLI arguments
    for key, value in kwargs.items():
        cmd.append(f"--{key}={value}")

    # Print summary
    print("🚀 Running SWE-agent (mixed batch mode)")
    print(f"   Total instances: {len(expanded_instances)}")
    print(f"   Original tasks: {len(original_instances)}")
    print(f"   Model/mode combinations: {len(model_configs)}")
    print(f"   Passes per combination: {passes}")
    print(f"   Output: {output_dir}")
    print(f"   Workers: {num_workers}")
    print()
    for model_name, mode_name, enable_ask, full_info in model_configs:
        mode_desc = mode_name
        if enable_ask:
            mode_desc += " (ask_human)"
        elif full_info:
            mode_desc += " (full info in prompt)"
        print(f"   📦 {model_name}: {mode_desc}")
    print()

    def _run_batch(ask_human_server=None, business_info_server=None):
        """Inner function to run the batch, optionally with tool servers."""
        env = os.environ.copy()
        sweagent_root = str((project_root / "SWE-agent").resolve())
        existing_pythonpath = env.get("PYTHONPATH", "")
        env["PYTHONPATH"] = (
            f"{sweagent_root}:{existing_pythonpath}" if existing_pythonpath else sweagent_root
        )
        if ask_human_server and needs_ask_human:
            # SQL runs locally (no Docker), SWE runs in Docker
            if task_type == "sql":
                env["ASK_HUMAN_SERVER_URL"] = ask_human_server.url
            else:
                env["ASK_HUMAN_SERVER_URL"] = (
                    f"http://host.docker.internal:{ask_human_server.port}/ask"
                )
        if business_info_server and task_type in ("sql", "add_business_info"):
            env["GET_BUSINESS_INFO_SERVER_URL"] = business_info_server.url

        # For SQL task type runs, set DATABASE_DESCRIPTIONS_BASE_DIR, CHROMA_PATH, and model cache paths.
        # DATABASE_DESCRIPTIONS_BASE_DIR is the parent directory containing per-task
        # subdirectories (each with table_descriptions.csv and per-table CSVs).
        # sql_tools.py resolves DATABASE_DESCRIPTIONS_DIR per-instance from
        # DATABASE_DESCRIPTIONS_BASE_DIR + TASK_INSTANCE_ID so each task gets its own
        # schema descriptions.
        if task_type in ("sql", "add_business_info") and original_instances:
            first_ps = original_instances[0].get("problem_statement", {})
            task_dir = None
            if isinstance(first_ps, dict):
                if first_ps.get("table_descriptions_path"):
                    descriptions_path = Path(first_ps["table_descriptions_path"])
                    task_dir = descriptions_path.parent.resolve()
                    if "DATABASE_DESCRIPTIONS_DIR" in env:
                        print(
                            "   📁 Preserving caller-provided DATABASE_DESCRIPTIONS_DIR: "
                            f"{env['DATABASE_DESCRIPTIONS_DIR']}"
                        )
                    else:
                        env["DATABASE_DESCRIPTIONS_DIR"] = str(task_dir)
                        print(
                            "   📁 Database descriptions (first task fallback): "
                            f"{env['DATABASE_DESCRIPTIONS_DIR']}"
                        )
                    if "DATABASE_DESCRIPTIONS_BASE_DIR" not in env:
                        env["DATABASE_DESCRIPTIONS_BASE_DIR"] = str(task_dir.parent)
                        print(
                            f"   📁 Database descriptions base: {env['DATABASE_DESCRIPTIONS_BASE_DIR']}"
                        )
            first_env = original_instances[0].get("env", {})
            require_buffed_chroma = env.get(REQUIRE_BUFFED_CHROMA_ENV) == "1"
            caller_has_chroma = "CHROMA_PATH" in env or "CHROMA_BASE_PATH" in env
            chroma_path = first_env.get("chroma_path", "")
            if caller_has_chroma:
                if "CHROMA_PATH" in env:
                    print(f"   📁 Preserving caller-provided CHROMA_PATH: {env['CHROMA_PATH']}")
                if "CHROMA_BASE_PATH" in env:
                    print(
                        "   📁 Preserving caller-provided CHROMA_BASE_PATH: "
                        f"{env['CHROMA_BASE_PATH']}"
                    )
                env.setdefault("CHROMA_COLLECTION_NAME", "business_info")
                if require_buffed_chroma and "CHROMA_PATH" in env:
                    if not Path(env["CHROMA_PATH"]).exists():
                        print(
                            "❌ Required buffed CHROMA_PATH does not exist: "
                            f"{env['CHROMA_PATH']}",
                            file=sys.stderr,
                        )
                        return 1, None
            elif require_buffed_chroma:
                print(
                    "❌ Required buffed ChromaDB env missing. "
                    "Caller must provide CHROMA_PATH/CHROMA_BASE_PATH.",
                    file=sys.stderr,
                )
                return 1, None
            elif chroma_path and Path(chroma_path).exists():
                env["CHROMA_PATH"] = str(Path(chroma_path).resolve())
                env.setdefault("CHROMA_COLLECTION_NAME", "business_info")
                print(
                    f"   📁 Using ChromaDB from: {env['CHROMA_PATH']} (collection: {env['CHROMA_COLLECTION_NAME']})"
                )
            else:
                chroma_dir = task_dir / "chroma_db" if task_dir is not None else None
                if chroma_dir and chroma_dir.exists():
                    env["CHROMA_PATH"] = str(chroma_dir)
                    env["CHROMA_COLLECTION_NAME"] = "business_info"
                    print(
                        f"   📁 Using ChromaDB from: {env['CHROMA_PATH']} (collection: {env['CHROMA_COLLECTION_NAME']})"
                    )
            local_hf_cache = "/tmp/hf_cache"
            if os.path.isdir(local_hf_cache):
                env["HF_HOME"] = local_hf_cache
            else:
                if not env.get("HF_HOME"):
                    env["HF_HOME"] = os.path.expanduser("~/.cache/huggingface")
            if not env.get("HUGGINGFACE_HUB_CACHE"):
                env["HUGGINGFACE_HUB_CACHE"] = env["HF_HOME"]
            if not env.get("TRANSFORMERS_CACHE"):
                env["TRANSFORMERS_CACHE"] = env["HF_HOME"]
            if not env.get("SENTENCE_TRANSFORMERS_HOME"):
                env["SENTENCE_TRANSFORMERS_HOME"] = env["HF_HOME"]

        try:
            result = subprocess.run(cmd, check=True, env=env, cwd=project_root)
            return result.returncode, None
        except subprocess.CalledProcessError as e:
            print(f"❌ SWE-agent failed with exit code {e.returncode}", file=sys.stderr)
            return e.returncode, None
        except KeyboardInterrupt:
            print("\n⚠️  Interrupted by user", file=sys.stderr)
            return 130, None

    ask_human_logs = None
    returncode = 0

    try:
        try:
            with ExitStack() as stack:
                ask_human_server = None
                business_info_server = None

                if task_type in ("sql", "add_business_info"):
                    business_info_server = stack.enter_context(
                        start_business_info_server(capture_output=False, verbose=True)
                    )

                if needs_ask_human:
                    # For SQL tasks, pass blockers directly (keyed by instance_id).
                    # For SWE tasks, use tasks_dir (server scans for blocker_registry.json).
                    server_kwargs = {
                        "capture_output": False,
                        "verbose": True,
                    }
                    if task_type == "sql" and sql_blockers_dict:
                        server_kwargs["blockers"] = sql_blockers_dict
                    else:
                        server_kwargs["tasks_dir"] = task_folder
                    ask_human_server = stack.enter_context(start_ask_human_server(**server_kwargs))

                returncode, _ = _run_batch(
                    ask_human_server=ask_human_server,
                    business_info_server=business_info_server,
                )

                # Get logs before ask_human server exits.
                if ask_human_server:
                    ask_human_logs = ask_human_server.get_logs()
                    if ask_human_logs:
                        print(f"✅ Retrieved ask_human logs for {len(ask_human_logs)} instances")
                        logs_file = output_dir / "ask_human_logs.json"
                        logs_file.write_text(json.dumps(ask_human_logs, indent=2))
                        print(f"   Saved to {logs_file}")
                    else:
                        print("⚠️  No ask_human logs found (agent may not have used the tool)")
        except (AskHumanServerError, BusinessInfoServerError) as e:
            print(f"❌ {e}", file=sys.stderr)
            return 1, None
    finally:
        # Clean up temp file
        if expanded_instances_path.exists():
            expanded_instances_path.unlink()
        # Also cleanup containers at end-of-run to prevent buildup during long pipelines.
        if cleanup_docker:
            cleanup_stale_docker_containers()

    return returncode, ask_human_logs


def _reorganize_mixed_results(
    results_dir: Path,
    model_configs: list[tuple[str, str, bool, bool]],
    passes: int,
):
    """
    Reorganize results from a mixed batch run into model/mode/pass structure.

    After a mixed sweagent run, instance directories are named like:
    {original_id}__{model_safe}__{mode_safe}[__pass_{n}]

    This function moves them to:
    {model}/{mode}/[pass_{n}/]{original_id}__{model_safe}__{mode_safe}[__pass_{n}]/

    The full instance ID (including model/mode/pass suffix) is preserved as the
    directory name and as the preds.json key so that all downstream lookups
    (traj files, ask_human_logs, eval results) use a consistent naming scheme.
    """
    import shutil

    # Create directory structure
    for model_name, mode_name, _, _ in model_configs:
        model_safe = model_name.replace("/", "_").replace(":", "_")
        mode_dir = results_dir / model_safe / mode_name
        mode_dir.mkdir(parents=True, exist_ok=True)

        if passes > 1:
            for pass_num in range(1, passes + 1):
                (mode_dir / f"pass_{pass_num}").mkdir(exist_ok=True)

    # Move trajectory directories to appropriate locations
    for item in results_dir.iterdir():
        if not item.is_dir():
            continue
        if item.name.startswith("."):
            continue

        # Parse the directory name to extract components
        # Format: {original_id}__{model_safe}__{mode_safe}[__pass_{n}]
        name = item.name

        # Skip directories that are already model dirs
        if any(
            name == model.replace("/", "_").replace(":", "_") for model, _, _, _ in model_configs
        ):
            continue

        # Try to parse the instance directory name
        parts = name.split("__")
        if len(parts) < 3:
            continue

        # Check if last part is pass info
        pass_num = 1
        if parts[-1].startswith("pass_"):
            try:
                pass_num = int(parts[-1][5:])
                parts = parts[:-1]
            except ValueError:
                pass

        if len(parts) < 3:
            continue

        # Last two parts are model and mode
        mode_safe = parts[-1]
        model_safe = parts[-2]
        original_id = "__".join(parts[:-2])

        # Find matching model config
        target_model = None
        target_mode = None
        for model_name, mode_name, _, _ in model_configs:
            if model_name.replace("/", "_").replace(":", "_") == model_safe:
                if mode_name.replace("-", "_") == mode_safe:
                    target_model = model_safe
                    target_mode = mode_name
                    break

        if not target_model or not target_mode:
            continue

        # Determine destination
        if passes > 1:
            dest_dir = results_dir / target_model / target_mode / f"pass_{pass_num}"
        else:
            dest_dir = results_dir / target_model / target_mode

        # Keep the full instance directory name (including model/mode/pass suffix)
        # so traj files inside the directory match the directory name exactly.
        dest = dest_dir / name
        if dest.exists():
            shutil.rmtree(dest)

        try:
            shutil.move(str(item), str(dest))
        except Exception as e:
            print(f"⚠️  Failed to move {item} to {dest}: {e}")

    # Handle preds.json - split by model/mode/pass
    preds_file = results_dir / "preds.json"
    if preds_file.exists():
        with open(preds_file, "r") as f:
            all_preds = json.load(f)

        # Group predictions by model/mode/pass
        preds_by_config: dict[tuple[str, str, int], dict] = {}
        for model_name, mode_name, _, _ in model_configs:
            model_safe = model_name.replace("/", "_").replace(":", "_")
            for pass_num in range(1, passes + 1):
                preds_by_config[(model_safe, mode_name, pass_num)] = {}

        for instance_id, pred_data in all_preds.items():
            # Parse instance ID
            parts = instance_id.split("__")
            if len(parts) < 3:
                continue

            pass_num = 1
            if parts[-1].startswith("pass_"):
                try:
                    pass_num = int(parts[-1][5:])
                    parts = parts[:-1]
                except ValueError:
                    pass

            if len(parts) < 3:
                continue

            mode_safe = parts[-1]
            model_safe = parts[-2]
            original_id = "__".join(parts[:-2])

            # Find matching mode name
            target_mode = None
            for _, mode_name, _, _ in model_configs:
                if mode_name.replace("-", "_") == mode_safe:
                    target_mode = mode_name
                    break

            if target_mode:
                key = (model_safe, target_mode, pass_num)
                if key in preds_by_config:
                    # Store under the ORIGINAL full instance_id (with pass suffix if present).
                    # This keeps preds.json keys consistent with:
                    # - the directory name (which also retains the full instance_id)
                    # - the traj file stem inside that directory
                    # - the ask_human_logs.json keys (keyed by TASK_INSTANCE_ID = full id)
                    # - the eval results dict keys (from calculate_pass_at_1/calculate_sql_pass_at_1)
                    preds_by_config[key][instance_id] = pred_data

        # Write per-config preds files
        for (model_safe, mode_name, pass_num), preds in preds_by_config.items():
            if passes > 1:
                preds_path = (
                    results_dir / model_safe / mode_name / f"pass_{pass_num}" / "preds.json"
                )
            else:
                preds_path = results_dir / model_safe / mode_name / "preds.json"

            preds_path.parent.mkdir(parents=True, exist_ok=True)
            with open(preds_path, "w") as f:
                json.dump(preds, f, indent=2)

        # Remove the combined preds file
        preds_file.unlink()
