#!/usr/bin/env bash
set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
BUILD_LOCAL_SIDECARS=0
NO_CACHE=0

if [[ "${1:-}" == "--build-local-sidecars" ]]; then
  BUILD_LOCAL_SIDECARS=1
  shift
fi

if [[ "${1:-}" == "--no-cache" ]]; then
  NO_CACHE=1
  shift
fi

python - "$SCRIPT_DIR" "$BUILD_LOCAL_SIDECARS" "$NO_CACHE" "$@" <<'PY'
import json
import os
import shlex
import shutil
import subprocess
import sys
import tempfile
from pathlib import Path

root = Path(sys.argv[1])
build_local_sidecars = sys.argv[2] == "1"
no_cache = sys.argv[3] == "1"
dataset_names = sys.argv[4:]

sidecar_manifest = root / "shared" / "sidecar_image_refs.json"
if not sidecar_manifest.exists():
    raise SystemExit(f"Missing sidecar manifest: {sidecar_manifest}")

defaults_path = root / "shared" / "image_source_defaults.json"
defaults = json.loads(defaults_path.read_text()) if defaults_path.exists() else {}
default_hf_bucket = str(defaults.get("default_hf_bucket", "")).strip()
local_archive_root_env = str(
    defaults.get("local_archive_root_env", "HILBENCH_SWE_IMAGE_ARCHIVE_ROOT")
).strip()
hf_bucket_override_env = str(
    defaults.get("hf_bucket_override_env", "HILBENCH_SWE_HF_BUCKET")
).strip()

local_archive_root = os.environ.get(local_archive_root_env, "").strip()
hf_bucket_override = os.environ.get(hf_bucket_override_env, "").strip()

sidecar_data = json.loads(sidecar_manifest.read_text())
sidecar_images = sidecar_data.get("images", {})
uv_cache_dir = root / ".uv-cache"
uv_cache_dir.mkdir(parents=True, exist_ok=True)


def run(cmd: list[str], *, env: dict[str, str] | None = None) -> None:
    print("+", shlex.join(cmd))
    subprocess.run(cmd, check=True, env=env)


def run_shell(command: str) -> None:
    print("+", command)
    subprocess.run(command, shell=True, check=True)


def ensure_hf_command() -> tuple[list[str], dict[str, str] | None]:
    if shutil.which("uvx"):
        env = dict(os.environ)
        env["UV_CACHE_DIR"] = str(uv_cache_dir)
        return ["uvx", "hf"], env
    if shutil.which("hf"):
        return ["hf"], None
    raise SystemExit("Neither `hf` nor `uvx` is available for HF bucket downloads.")


def docker_image_exists(ref: str) -> bool:
    inspect = subprocess.run(
        ["docker", "image", "inspect", ref],
        check=False,
        capture_output=True,
        text=True,
    )
    return inspect.returncode == 0


def load_archive(archive_path: Path) -> None:
    run_shell(f"zstd -dc {shlex.quote(str(archive_path))} | docker load")


def resolve_hf_bucket(image_archive: dict) -> str:
    return (
        hf_bucket_override
        or str(image_archive.get("hf_bucket") or "").strip()
        or default_hf_bucket
    )


for server_name, ref in sidecar_images.items():
    if docker_image_exists(ref):
        print(f"Using existing local sidecar image for {server_name}: {ref}")
        continue

    if build_local_sidecars:
        context_dir = root / "shared" / "mcp-servers" / server_name
        server_py = context_dir / "server.py"
        if context_dir.exists() and server_py.exists():
            cmd = ["docker", "buildx", "build", "--load"]
            if no_cache:
                cmd.append("--no-cache")
            cmd.extend(["-t", ref, str(context_dir)])
            run(cmd)
            continue

        print(
            f"Local build context for {server_name} is incomplete at {context_dir}; "
            f"falling back to docker pull for {ref}.",
            file=sys.stderr,
        )

    run(["docker", "pull", ref])


for dataset_name in dataset_names:
    image_ref_path = root / dataset_name / "shared" / "image_ref.txt"
    if not image_ref_path.exists():
        continue

    image_ref = image_ref_path.read_text().strip()
    if not image_ref:
        continue

    if docker_image_exists(image_ref):
        print(f"Using existing local Docker image for {dataset_name}: {image_ref}")
        continue

    image_archive_path = root / dataset_name / "shared" / "image_archive.json"
    if not image_archive_path.exists():
        run(["docker", "pull", image_ref])
        continue

    image_archive = json.loads(image_archive_path.read_text())
    artifact_path = str(image_archive.get("artifact_path", "")).strip()
    if not artifact_path:
        run(["docker", "pull", image_ref])
        continue

    local_override_archive = None
    if local_archive_root:
        candidate = Path(local_archive_root) / artifact_path
        if candidate.exists():
            local_override_archive = candidate
        else:
            print(
                "Local archive override was set but the archive was not found:",
                candidate,
                file=sys.stderr,
            )

    if local_override_archive is not None:
        print(f"Loading {dataset_name} from local archive override: {local_override_archive}")
        load_archive(local_override_archive)
        continue

    artifact_abspath = str(image_archive.get("artifact_abspath", "")).strip()
    if artifact_abspath:
        print(
            "Ignoring artifact_abspath for runtime resolution; set "
            f"{local_archive_root_env} to reuse a local archive tree.",
            file=sys.stderr,
        )

    hf_bucket = resolve_hf_bucket(image_archive)
    if not hf_bucket:
        raise SystemExit(
            f"No HF bucket configured for {dataset_name}; checked metadata and {defaults_path}"
        )

    hf_src = f"hf://buckets/{hf_bucket}/{artifact_path}"
    hf_cmd, hf_env = ensure_hf_command()
    with tempfile.TemporaryDirectory(prefix=f"{dataset_name}-image-", dir=root) as tmp_dir:
        local_archive = Path(tmp_dir) / Path(artifact_path).name
        run([*hf_cmd, "buckets", "cp", hf_src, str(local_archive)], env=hf_env)
        print(f"Loading {dataset_name} from HF bucket: {hf_src}")
        load_archive(local_archive)
PY
