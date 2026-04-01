"""
Shared utilities for loading task instances from directory structure.
"""

import json
from pathlib import Path
from typing import Any


def load_instance_from_task_dir(
    task_dir: Path,
    augment_blockers_fn: Any | None = None,
) -> dict[str, Any]:
    """
    Load an instance from a task directory.

    This is the canonical function for loading task metadata and creating
    an instance dict suitable for SWE-agent.

    Args:
        task_dir: Path to task directory containing metadata.json, problem_statement.txt, etc.
        augment_blockers_fn: Optional function to augment problem statement with blockers.
                            If provided, will be called as augment_blockers_fn(problem_statement, task_dir).

    Returns:
        Instance dict with all required and optional fields.

    Raises:
        FileNotFoundError: If problem_statement.txt is not found.
    """
    # Load metadata (optional - defaults to using directory name as instance_id)
    metadata_path = task_dir / "metadata.json"
    if metadata_path.exists():
        metadata = json.loads(metadata_path.read_text())
    else:
        metadata = {"instance_id": task_dir.name}

    # Load problem statement (required)
    problem_path = task_dir / "problem_statement.txt"
    if problem_path.exists():
        problem_statement = problem_path.read_text()
    else:
        raise FileNotFoundError(f"No problem_statement.txt found in {task_dir}")

    # Augment problem statement with blockers if requested
    if augment_blockers_fn is not None:
        problem_statement = augment_blockers_fn(problem_statement, task_dir)

    # Determine repo source: local path or GitHub URL
    metadata_repo_name = metadata.get("repo_name", "")
    print(f"[instance_utils] metadata_repo_name = {metadata_repo_name!r} from {metadata_path}")
    if metadata_repo_name == "app":  # trigger PreExistingRepoConfig in SWE-agent
        repo_spec = "app"
    else:
        local_repo_path = task_dir / "app"
        if not (local_repo_path.exists() and local_repo_path.is_dir()):
            local_repo_path = task_dir / "repo"

        if local_repo_path.exists() and local_repo_path.is_dir():
            # Use local repo path (pre-cloned and pre-installed)
            repo_spec = str(local_repo_path.absolute())
        else:
            # Fall back to GitHub URL from metadata
            repo_url = metadata.get("repo_clone_url", metadata.get("repo_url", ""))
            if not repo_url and "repo" in metadata:
                # Construct URL from repo field (e.g., "django/django")
                repo_url = f"https://github.com/{metadata['repo']}.git"
            repo_spec = repo_url

    # Create instance with required fields
    instance: dict[str, Any] = {
        "instance_id": metadata.get("instance_id", task_dir.name),
        "problem_statement": problem_statement,
        "repo_name": repo_spec,
        "base_commit": metadata.get("base_commit", ""),
        "image_name": metadata.get("image_name", "sweagent/swe-agent:latest"),
    }

    # Add post_startup_commands if present in metadata
    if "post_startup_commands" in metadata:
        instance["post_startup_commands"] = metadata["post_startup_commands"]
        instance["post_startup_command_timeout"] = metadata.get("post_startup_command_timeout", 900)

    # Add any additional metadata fields that aren't already in instance
    for key, value in metadata.items():
        if key not in instance:
            instance[key] = value

    return instance


def extract_original_instance_id(
    instance_id: str,
    model: str | None = None,
    mode: str | None = None,
    pass_num: int | None = None,
) -> str:
    """
    Extract the original instance ID by stripping various suffixes.

    Handles two patterns:
    1. Model/mode/pass suffixes: {original_id}__{model}__{mode}[__pass_{pass_num}]
    2. Blocker config suffixes: {original_id}__blocker_config__{config_name}

    Args:
        instance_id: The (potentially modified) instance_id
        model: Model name (for model/mode/pass pattern)
        mode: Mode name (for model/mode/pass pattern)
        pass_num: Pass number (for model/mode/pass pattern)

    Returns:
        The original instance_id without suffixes
    """
    # First, handle blocker test configuration suffix
    blocker_config_sep = "__blocker_config__"
    if blocker_config_sep in instance_id:
        instance_id = instance_id.split(blocker_config_sep)[0]

    # Handle model/mode/pass suffixes if parameters provided
    if model is not None and mode is not None:
        model_safe = model.replace("/", "_").replace(":", "_")
        mode_safe = mode.replace("-", "_")

        # Try different suffix patterns
        suffixes = []
        if pass_num is not None:
            suffixes.extend(
                [
                    f"__{model_safe}__{mode}__pass_{pass_num}",
                    f"__{model_safe}__{mode_safe}__pass_{pass_num}",
                ]
            )
        suffixes.extend(
            [
                f"__{model_safe}__{mode}",
                f"__{model_safe}__{mode_safe}",
            ]
        )

        for suffix in suffixes:
            if instance_id.endswith(suffix):
                return instance_id[: -len(suffix)]

    return instance_id
