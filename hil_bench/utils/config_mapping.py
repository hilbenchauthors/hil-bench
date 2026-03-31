from __future__ import annotations

import os
from pathlib import Path
from typing import Any

import yaml

VALID_TASK_TYPES = {"sql", "swe"}
VALID_MODES = {"baseline", "ask_human", "full_info"}
VALID_AGENT_HOSTING_TYPES = {"litellm_proxy", "provider_direct", "self_hosted"}
VALID_JUDGE_HOSTING_TYPES = {"litellm_proxy", "provider_direct", "self_hosted"}


def _load_yaml(path: Path) -> dict[str, Any]:
    if not path.exists():
        raise FileNotFoundError(f"Config file not found: {path}")
    raw = yaml.safe_load(path.read_text()) or {}
    if not isinstance(raw, dict):
        raise ValueError(f"Expected YAML object in {path}")
    return raw


def _resolve_path(raw_path: str, *, mapping_file: Path, project_root: Path) -> Path:
    candidate = Path(raw_path)
    if candidate.is_absolute():
        return candidate
    rel_to_mapping = (mapping_file.parent / candidate).resolve()
    if rel_to_mapping.exists():
        return rel_to_mapping
    return (project_root / candidate).resolve()


def load_config_mapping(mapping_file: str | Path, project_root: str | Path) -> dict[str, Any]:
    """Load and validate mapping YAML for task_type/mode/model agent configs."""
    mapping_path = Path(mapping_file).resolve()
    project_root = Path(project_root).resolve()
    raw = _load_yaml(mapping_path)

    for task_type, task_type_data in raw.items():
        if task_type not in VALID_TASK_TYPES:
            raise ValueError(
                f"Invalid task_type key '{task_type}' in {mapping_path}. "
                f"Expected one of: {sorted(VALID_TASK_TYPES)}"
            )
        if not isinstance(task_type_data, dict):
            raise ValueError(f"Expected mapping under '{task_type}' in {mapping_path}")
        for mode, mode_data in task_type_data.items():
            if mode not in VALID_MODES:
                raise ValueError(
                    f"Invalid mode key '{task_type}.{mode}' in {mapping_path}. "
                    f"Expected one of: {sorted(VALID_MODES)}"
                )
            if not isinstance(mode_data, dict):
                raise ValueError(f"Expected model->path mapping under '{task_type}.{mode}'")
            for model_name, config_path in mode_data.items():
                if not isinstance(config_path, str) or not config_path.strip():
                    raise ValueError(
                        f"Invalid config path for '{task_type}.{mode}.{model_name}' in {mapping_path}"
                    )
                resolved = _resolve_path(
                    config_path.strip(), mapping_file=mapping_path, project_root=project_root
                )
                if not resolved.exists():
                    raise FileNotFoundError(
                        f"Mapped config not found for '{task_type}.{mode}.{model_name}': {resolved}"
                    )
    return raw


def resolve_agent_config_path(
    mapping: dict[str, Any],
    *,
    task_type: str,
    mode: str,
    model_name: str,
    mapping_file: str | Path,
    project_root: str | Path,
) -> Path:
    """Resolve config path for a concrete task_type/mode/model key."""
    try:
        model_map = mapping[task_type][mode]
    except KeyError as exc:
        raise KeyError(f"Missing mapping section '{task_type}.{mode}'") from exc
    if model_name not in model_map:
        raise KeyError(
            f"Missing mapping for '{task_type}.{mode}.{model_name}'. "
            f"Available models: {sorted(model_map.keys())}"
        )
    raw_path = model_map[model_name]
    if not isinstance(raw_path, str) or not raw_path.strip():
        raise ValueError(f"Invalid mapping path for '{task_type}.{mode}.{model_name}'")
    resolved = _resolve_path(
        raw_path.strip(),
        mapping_file=Path(mapping_file).resolve(),
        project_root=Path(project_root).resolve(),
    )
    if not resolved.exists():
        raise FileNotFoundError(
            f"Resolved config path for '{task_type}.{mode}.{model_name}' does not exist: {resolved}"
        )
    return resolved


def load_and_apply_judge_config(judge_config_path: str | Path) -> None:
    """Load judge config YAML and apply ASK_HUMAN_* environment variables."""
    path = Path(judge_config_path).resolve()
    raw = _load_yaml(path)

    hosting = raw.get("hosting")
    if not isinstance(hosting, dict):
        raise ValueError(
            f"Judge config must declare top-level `hosting` object: {path}"
        )
    host_type_raw = hosting.get("type")
    if host_type_raw is None:
        raise ValueError(f"Judge config missing `hosting.type`: {path}")
    host_type = str(host_type_raw).strip().lower().replace("-", "_")
    if host_type not in VALID_JUDGE_HOSTING_TYPES:
        raise ValueError(
            f"Unsupported judge hosting.type '{host_type}' in {path}. "
            f"Expected one of: {sorted(VALID_JUDGE_HOSTING_TYPES)}"
        )

    model = str(raw.get("model", "casperhansen/llama-3.3-70b-instruct-awq")).strip()
    if model:
        os.environ["ASK_HUMAN_MODEL"] = os.path.expandvars(model)
        os.environ["ASK_HUMAN_SELF_HOSTED_MODEL"] = os.path.expandvars(model)

    def _set_if_present(env_name: str, value: Any) -> None:
        if value is not None and str(value).strip():
            os.environ[env_name] = os.path.expandvars(str(value).strip())

    os.environ["ASK_HUMAN_HOSTING_TYPE"] = host_type
    if host_type in {"litellm_proxy", "provider_direct"}:
        os.environ["ASK_HUMAN_PROVIDER"] = "litellm"
    else:
        os.environ["ASK_HUMAN_PROVIDER"] = "self_hosted"

    if host_type == "litellm_proxy":
        litellm_base_url = hosting.get("litellm_base_url")
        litellm_base_url_env = hosting.get("litellm_base_url_env")
        if litellm_base_url_env is not None and str(litellm_base_url_env).strip():
            env_name = str(litellm_base_url_env).strip()
            litellm_base_url = os.getenv(env_name, "")
            if not str(litellm_base_url).strip():
                raise ValueError(
                    f"Judge config expects env var '{env_name}' but it is not set ({path})"
                )
        if litellm_base_url is None or not str(litellm_base_url).strip():
            raise ValueError(
                "Judge hosting.type=litellm_proxy requires "
                f"hosting.litellm_base_url or hosting.litellm_base_url_env: {path}"
            )
        _set_if_present("ASK_HUMAN_LITELLM_BASE_URL", litellm_base_url)

    if host_type == "self_hosted":
        self_hosted_base_url = hosting.get("self_hosted_base_url")
        self_hosted_base_url_env = hosting.get("self_hosted_base_url_env")
        if self_hosted_base_url_env is not None and str(self_hosted_base_url_env).strip():
            env_name = str(self_hosted_base_url_env).strip()
            self_hosted_base_url = os.getenv(env_name, "")
            if not str(self_hosted_base_url).strip():
                raise ValueError(
                    f"Judge config expects env var '{env_name}' but it is not set ({path})"
                )
        if self_hosted_base_url is None or not str(self_hosted_base_url).strip():
            raise ValueError(
                "Judge hosting.type=self_hosted requires "
                f"hosting.self_hosted_base_url or hosting.self_hosted_base_url_env: {path}"
            )
        _set_if_present("ASK_HUMAN_SELF_HOSTED_BASE_URL", self_hosted_base_url)

        self_hosted_api_key = hosting.get("self_hosted_api_key")
        if self_hosted_api_key is not None and str(self_hosted_api_key).strip():
            _set_if_present("ASK_HUMAN_SELF_HOSTED_API_KEY", self_hosted_api_key)

        key_env = hosting.get("self_hosted_api_key_env")
        if key_env is not None and str(key_env).strip():
            key_env_name = str(key_env).strip()
            key_value = os.getenv(key_env_name, "").strip()
            if not key_value:
                raise ValueError(
                    f"Judge config expects env var '{key_env_name}' but it is not set ({path})"
                )
            os.environ["ASK_HUMAN_SELF_HOSTED_API_KEY"] = key_value


def validate_agent_hosting_config(config_path: str | Path) -> str:
    path = Path(config_path).resolve()
    raw = _load_yaml(path)
    hosting = raw.get("hosting")
    if not isinstance(hosting, dict):
        raise ValueError(
            f"Agent config must declare a top-level `hosting` object: {path}"
        )
    host_type_raw = hosting.get("type")
    if host_type_raw is None:
        raise ValueError(f"Agent config missing `hosting.type`: {path}")
    host_type = str(host_type_raw).strip().lower().replace("-", "_")
    if host_type not in VALID_AGENT_HOSTING_TYPES:
        raise ValueError(
            f"Unsupported hosting.type '{host_type}' in {path}. "
            f"Expected one of: {sorted(VALID_AGENT_HOSTING_TYPES)}"
        )

    agent = raw.get("agent")
    if not isinstance(agent, dict):
        raise ValueError(f"Agent config missing top-level `agent` object: {path}")
    model = agent.get("model", {})
    if not isinstance(model, dict):
        raise ValueError(f"Agent config missing `agent.model` object: {path}")

    api_base = str(model.get("api_base") or "").strip()
    api_base = os.path.expandvars(api_base)
    api_base_env = hosting.get("api_base_env")
    api_base_from_env = ""
    if api_base_env is not None and str(api_base_env).strip():
        env_name = str(api_base_env).strip()
        api_base_from_env = os.getenv(env_name, "").strip()
        if not api_base_from_env:
            raise ValueError(
                f"Agent config expects env var '{env_name}' but it is not set: {path}"
            )
    litellm_base_url = os.getenv("LITELLM_BASE_URL", "").strip()

    if host_type == "litellm_proxy":
        if api_base or api_base_from_env:
            raise ValueError(
                "hosting.type=litellm_proxy requires agent.model.api_base and hosting.api_base_env "
                f"to be unset: {path}"
            )
        if not litellm_base_url:
            raise ValueError(
                f"hosting.type=litellm_proxy requires LITELLM_BASE_URL to be set: {path}"
            )
    elif host_type == "provider_direct":
        if api_base or api_base_from_env:
            raise ValueError(
                "hosting.type=provider_direct requires agent.model.api_base and hosting.api_base_env "
                f"to be unset: {path}"
            )
        if litellm_base_url:
            raise ValueError(
                "hosting.type=provider_direct is ambiguous when LITELLM_BASE_URL is set. "
                f"Unset LITELLM_BASE_URL or switch hosting.type in {path}"
            )
    elif host_type == "self_hosted":
        if not api_base and not api_base_from_env:
            raise ValueError(
                "hosting.type=self_hosted requires agent.model.api_base or hosting.api_base_env "
                f"to be set: {path}"
            )

    return host_type
