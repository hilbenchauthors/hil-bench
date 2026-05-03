#!/usr/bin/env bash
# warmup_data.sh — Download SQL task databases and description CSVs from HuggingFace.
#
# For each SQL task directory (or the named datasets given as arguments), reads
# shared/data_archive.json and downloads the SQLite database + description CSVs
# into shared/data/, skipping any files that already exist.
#
# Usage:
#   ./warmup_data.sh                          # warm up all sql_* datasets
#   ./warmup_data.sh sql_3 sql_7 sql_42       # warm up specific datasets
#
# Environment variables:
#   HF_TOKEN   — HuggingFace token (if not already logged in via `hf login`)
set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"

# Run via uv with huggingface_hub from public PyPI — no pre-existing venv needed.
# UV_INDEX_URL overrides any project-local registry (e.g. private codeartifact) so
# that huggingface_hub is always resolved from the public package index.
UV_INDEX_URL=https://pypi.org/simple/ uv run --no-project --with huggingface_hub \
    python - "$SCRIPT_DIR" "$@" <<'PY'
import json
import sys
from pathlib import Path

import huggingface_hub

root = Path(sys.argv[1])
dataset_names = sys.argv[2:]

# If no specific datasets given, process all sql_* directories
if not dataset_names:
    dataset_names = sorted(
        d.name for d in root.iterdir()
        if d.is_dir() and d.name.startswith("sql_") and d.name[4:].isdigit()
    )

if not dataset_names:
    print("No sql_* dataset directories found under", root)
    sys.exit(0)


def cp_hf(hf_src: str, local_dest: Path) -> None:
    """Copy a single file from an HF bucket to a local path via huggingface_hub."""
    local_dest.parent.mkdir(parents=True, exist_ok=True)
    print(f"+ hf cp {hf_src} -> {local_dest}")
    fs = huggingface_hub.HfFileSystem()
    with fs.open(hf_src, "rb") as f:
        local_dest.write_bytes(f.read())


ok = []
skipped = []
errors = []

for dataset_name in dataset_names:
    dataset_dir = root / dataset_name
    archive_path = dataset_dir / "shared" / "data_archive.json"

    if not archive_path.exists():
        print(f"[skip] {dataset_name}: no data_archive.json at {archive_path}")
        skipped.append(dataset_name)
        continue

    archive = json.loads(archive_path.read_text())
    hf_bucket = archive["hf_bucket"]
    db_artifact = archive["db_artifact_path"]
    desc_artifacts = archive.get("desc_artifact_paths", [])

    data_dir = dataset_dir / "shared" / "data"
    desc_dir = data_dir / "database_description"
    db_dest = data_dir / "database.sqlite"

    try:
        # --- database.sqlite ---
        if db_dest.exists():
            print(f"[ok]   {dataset_name}: database.sqlite already present, skipping")
        else:
            hf_src = f"hf://buckets/{hf_bucket}/{db_artifact}"
            print(f"[dl]   {dataset_name}: downloading database.sqlite ...")
            cp_hf(hf_src, db_dest)

        # --- description CSVs ---
        for artifact_path in desc_artifacts:
            fname = Path(artifact_path).name
            dest = desc_dir / fname
            if dest.exists():
                print(f"[ok]   {dataset_name}: {fname} already present, skipping")
            else:
                hf_src = f"hf://buckets/{hf_bucket}/{artifact_path}"
                print(f"[dl]   {dataset_name}: downloading {fname} ...")
                cp_hf(hf_src, dest)

        ok.append(dataset_name)
        print(f"[done] {dataset_name}")

    except Exception as exc:
        print(f"[ERR]  {dataset_name}: {exc}", file=sys.stderr)
        errors.append(dataset_name)

print()
print(f"Done:    {len(ok)} dataset(s): {', '.join(ok) if ok else '(none)'}")
if skipped:
    print(f"Skipped: {len(skipped)} dataset(s): {', '.join(skipped)}")
if errors:
    print(f"Errors:  {len(errors)} dataset(s): {', '.join(errors)}", file=sys.stderr)
    sys.exit(1)
PY
