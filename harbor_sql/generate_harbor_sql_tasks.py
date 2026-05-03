"""
Generate Harbor SQL task directories from the ScaleAI/hil-bench HuggingFace dataset.

This script replaces the previous harbor_conversion/generate_harbor_sql_tasks.py whose
MongoDB-based retrieve_attempt_info() dependency is unavailable. Data is fetched directly
from the public HF dataset (ScaleAI/hil-bench) which contains all 100 public SQL tasks.

Usage examples:
  # Generate task at CSV index 3 (card_games, public_sql_3):
  uv run python harbor_sql/generate_harbor_sql_tasks.py --indices 3

  # Generate a task by attempt_id:
  uv run python harbor_sql/generate_harbor_sql_tasks.py --attempt-ids 6995e83741c6ec518b1b586b

  # Generate all 100 public tasks:
  uv run python harbor_sql/generate_harbor_sql_tasks.py --all

  # Generate with custom output dir:
  uv run python harbor_sql/generate_harbor_sql_tasks.py --indices 0 1 2 --output-dir /tmp/my_sql_tasks
"""

from __future__ import annotations

import argparse
import io
import json
import logging
import shutil
import sqlite3
import sys
import time
import traceback
import urllib.request
from collections import Counter
from pathlib import Path
from typing import Any

import pandas as pd

HARBOR_SQL_ROOT = Path(__file__).resolve().parent
HIL_BENCH_ROOT = HARBOR_SQL_ROOT.parent
REPO_ROOT = HIL_BENCH_ROOT.parent

UTILS_ROOT = REPO_ROOT / "research_evals" / "hil_bench" / "utils"
CSV_PATH = UTILS_ROOT / "sql_delivered_tasks_and_attempts_PUBLIC.csv"

SHARED_MCP_SERVERS_DIR = HARBOR_SQL_ROOT / "shared" / "mcp-servers"

HF_DATASET = "ScaleAI/hil-bench"
MODES = ("baseline", "ask_human", "full_info")

DEFAULT_OUTPUT_DIR = HARBOR_SQL_ROOT
MAX_QUERY_EXECUTION_TIMEOUT = 300

logger = logging.getLogger("harbor_sql.generate")


# ---------------------------------------------------------------------------
# Text templates (inline to avoid external template files dependency)
# ---------------------------------------------------------------------------

_INSTRUCTION_BASELINE_TMPL = """\
# Instructions
You are working in the `{database_name}` database.

Answer the following question:
{question}

# Available Commands
The following commands are installed in this terminal — run them directly from the shell.
**Only run ONE command per turn** — each command blocks until the MCP server responds.
- `get_database_info {database_name}` — list all tables and their descriptions
- `get_table_info {database_name} <table>` — list columns and descriptions for a table
- `get_column_info {database_name} <table> <column>` — get details for a specific column
- `get_business_info {database_name} "<question>"` — semantic search over business documentation
- `execute_sql "<query>"` — execute a SQL query against the database
{ask_human_line}- `submit_sql "<query>"` — submit your final SQL answer

# Submission Instructions
When you are confident your SQL query is correct, call the `submit_sql` tool with your final query as the argument. If you do not call `submit_sql`, the task will be considered incomplete and scored as 0.
"""

_INSTRUCTION_FULL_INFO_TMPL = """\
# Instructions
You are working in the `{database_name}` database.

Answer the following question:
{question}

## Additional Context
The following clarifications are provided to help you complete this task:

{blockers_section}

# Available Commands
The following commands are installed in this terminal — run them directly from the shell.
**Only run ONE command per turn** — each command blocks until the MCP server responds.
- `get_database_info {database_name}` — list all tables and their descriptions
- `get_table_info {database_name} <table>` — list columns and descriptions for a table
- `get_column_info {database_name} <table> <column>` — get details for a specific column
- `get_business_info {database_name} "<question>"` — semantic search over business documentation
- `execute_sql "<query>"` — execute a SQL query against the database
- `submit_sql "<query>"` — submit your final SQL answer

# Submission Instructions
When you are confident your SQL query is correct, call the `submit_sql` tool with your final query as the argument. If you do not call `submit_sql`, the task will be considered incomplete and scored as 0.
"""

_TASK_TOML_TMPL = """\
version = "1.0"

[metadata]
task_id = "{mode}"
task_type = "sql"
mode = "{mode}"
database_name = "{database_name}"
task_attempt_id = "{task_attempt_id}"
tags = ["sql", "{mode}", "hil-bench"]

[verifier]
timeout_sec = 300.0

[agent]
timeout_sec = 1800.0

[environment]
build_timeout_sec = 600.0
cpus = 2
memory_mb = 4096
storage_mb = 12288
gpus = 0
allow_internet = true

[[environment.mcp_servers]]
name = "sql-tools"
transport = "streamable-http"
url = "http://sql-tools:8000/mcp"

[[environment.mcp_servers]]
name = "business-info"
transport = "streamable-http"
url = "http://business-info:8000/mcp"
{ask_human_mcp_block}
"""

_ASK_HUMAN_MCP_BLOCK = """\

[[environment.mcp_servers]]
name = "ask-human"
transport = "streamable-http"
url = "http://ask-human:8000/mcp"
"""

_DOCKERFILE = """\
FROM python:3.11-slim
RUN mkdir -p /tmp/apt-dl/partial && apt-get update && apt-get install -y --no-install-recommends -o Dir::Cache::archives=/tmp/apt-dl sqlite3 curl tmux && rm -rf /tmp/apt-dl /var/lib/apt/lists/*
RUN pip install --no-cache-dir pandas
COPY mcp.py /usr/local/bin/mcp
RUN chmod +x /usr/local/bin/mcp
COPY setup_tools.py /tmp/setup_tools.py
RUN python3 /tmp/setup_tools.py && rm /tmp/setup_tools.py
WORKDIR /app
"""

_COMPOSE_NO_ASK_HUMAN = """\
services:
  main:
    depends_on:
      sql-tools:
        condition: service_healthy
      business-info:
        condition: service_healthy
    volumes:
      - ${CONTEXT_DIR:-.}/../../shared/data:/data:ro
      - harbor-shared:/harbor_shared

  sql-tools:
    image: hil-bench-harbor/sql-tools:latest
    pull_policy: never
    volumes:
      - ${CONTEXT_DIR:-.}/../../shared/data:/data:ro
      - harbor-shared:/harbor_shared
    environment:
      - DATA_DIR=/data
      - SUBMISSION_FILE=/harbor_shared/submitted_query.sql
    expose:
      - "8000"
    healthcheck:
      test: ["CMD", "python", "-c", "import socket; s=socket.create_connection(('localhost',8000),timeout=2); s.close()"]
      interval: 2s
      timeout: 5s
      retries: 15
      start_period: 5s

  business-info:
    image: hil-bench-harbor/business-info:latest
    pull_policy: never
    volumes:
      - ${CONTEXT_DIR:-.}/../../shared/data:/data:ro
    environment:
      - DATA_DIR=/data
    expose:
      - "8000"
    healthcheck:
      test: ["CMD", "python", "-c", "import socket; s=socket.create_connection(('localhost',8000),timeout=2); s.close()"]
      interval: 2s
      timeout: 10s
      retries: 30
      start_period: 30s

volumes:
  harbor-shared:
"""

_COMPOSE_ASK_HUMAN = """\
services:
  main:
    depends_on:
      sql-tools:
        condition: service_healthy
      business-info:
        condition: service_healthy
      ask-human:
        condition: service_healthy
    volumes:
      - ${CONTEXT_DIR:-.}/../../shared/data:/data:ro
      - harbor-shared:/harbor_shared

  sql-tools:
    image: hil-bench-harbor/sql-tools:latest
    pull_policy: never
    volumes:
      - ${CONTEXT_DIR:-.}/../../shared/data:/data:ro
      - harbor-shared:/harbor_shared
    environment:
      - DATA_DIR=/data
      - SUBMISSION_FILE=/harbor_shared/submitted_query.sql
    expose:
      - "8000"
    healthcheck:
      test: ["CMD", "python", "-c", "import socket; s=socket.create_connection(('localhost',8000),timeout=2); s.close()"]
      interval: 2s
      timeout: 5s
      retries: 15
      start_period: 5s

  business-info:
    image: hil-bench-harbor/business-info:latest
    pull_policy: never
    volumes:
      - ${CONTEXT_DIR:-.}/../../shared/data:/data:ro
    environment:
      - DATA_DIR=/data
    expose:
      - "8000"
    healthcheck:
      test: ["CMD", "python", "-c", "import socket; s=socket.create_connection(('localhost',8000),timeout=2); s.close()"]
      interval: 2s
      timeout: 10s
      retries: 30
      start_period: 30s

  ask-human:
    image: hil-bench-harbor/ask-human:latest
    pull_policy: never
    volumes:
      - ${CONTEXT_DIR:-.}/../../shared/ask-human-data:/ask-human-data:ro
      - harbor-shared:/harbor_shared
    environment:
      - BLOCKER_REGISTRY_PATH=/ask-human-data/blocker_registry.json
      - OUTPUT_DIR=/harbor_shared
      - ASK_HUMAN_BACKEND=${ASK_HUMAN_BACKEND:-litellm_proxy}
      - ASK_HUMAN_MODEL=${ASK_HUMAN_MODEL:-openai/gpt-4o}
      - LITELLM_API_KEY=${LITELLM_API_KEY:-}
      - LITELLM_BASE_URL=${LITELLM_BASE_URL:-}
      - OPENAI_API_KEY=${OPENAI_API_KEY:-}
      - OPENAI_BASE_URL=${OPENAI_BASE_URL:-}
      - ANTHROPIC_API_KEY=${ANTHROPIC_API_KEY:-}
      - GOOGLE_API_KEY=${GOOGLE_API_KEY:-}
      - VLLM_BASE_URL=${VLLM_BASE_URL:-}
      - VLLM_MODEL=${VLLM_MODEL:-}
      - VLLM_API_KEY=${VLLM_API_KEY:-}
    expose:
      - "8000"
    healthcheck:
      test: ["CMD", "python", "-c", "import socket; s=socket.create_connection(('localhost',8000),timeout=2); s.close()"]
      interval: 2s
      timeout: 5s
      retries: 15
      start_period: 5s

volumes:
  harbor-shared:
"""

_TEST_SH = """\
#!/usr/bin/env bash
REWARD_DIR="/logs/verifier"
mkdir -p "$REWARD_DIR"

_fail() {
    local msg="$1"
    echo "0" > "$REWARD_DIR/reward.txt"
    printf '{"solve": 0, "precision": 0.0, "recall": 0.0, "f1": 0.0, "error": "%s"}\\n' "$msg" \\
        > "$REWARD_DIR/reward.json"
}

python /tests/test_verify.py 2>&1
exit_code=$?

if [ "$exit_code" -ne 0 ]; then
    _fail "test_verify.py exited with code $exit_code"
    exit "$exit_code"
fi
"""

_SOLVE_SH = """\
#!/usr/bin/env bash
set -euo pipefail
cp /solution/ground_truth.sql /harbor_shared/submitted_query.sql
"""


# ---------------------------------------------------------------------------
# Template rendering
# ---------------------------------------------------------------------------

def _render_blockers(blockers: list[dict[str, Any]]) -> str:
    chunks: list[str] = []
    for blocker in blockers:
        chunks.append(f"### {blocker['description']}")
        chunks.append(str(blocker["resolution"]).strip())
        chunks.append("")
    return "\n".join(chunks).rstrip()


def _instruction_content(mode: str, database_name: str, question: str, blockers: list[dict]) -> str:
    if mode == "full_info":
        return _INSTRUCTION_FULL_INFO_TMPL.format(
            database_name=database_name,
            question=question,
            blockers_section=_render_blockers(blockers),
        ).rstrip() + "\n"
    # baseline and ask_human use the same base template; ask_human adds the ask_human command
    ask_human_line = (
        "- `ask_human \"<question>\"` — ask a specific clarifying question about a task blocker\n"
        if mode == "ask_human" else ""
    )
    return _INSTRUCTION_BASELINE_TMPL.format(
        database_name=database_name,
        question=question,
        ask_human_line=ask_human_line,
    ).rstrip() + "\n"


def _task_toml_content(mode: str, database_name: str, task_attempt_id: str) -> str:
    ask_block = _ASK_HUMAN_MCP_BLOCK if mode == "ask_human" else ""
    return _TASK_TOML_TMPL.format(
        mode=mode,
        database_name=database_name,
        task_attempt_id=task_attempt_id,
        ask_human_mcp_block=ask_block.rstrip(),
    ).rstrip() + "\n"


# ---------------------------------------------------------------------------
# File I/O helpers
# ---------------------------------------------------------------------------

def _write(path: Path, content: str) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(content)


def _write_bytes(path: Path, data: bytes) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_bytes(data)


def _download(url: str, dest: Path) -> None:
    logger.info("Downloading %s → %s", url, dest)
    dest.parent.mkdir(parents=True, exist_ok=True)
    if url.startswith("hf://"):
        from huggingface_hub import HfFileSystem
        fs = HfFileSystem()
        with fs.open(url, "rb") as f:
            _write_bytes(dest, f.read())
    else:
        with urllib.request.urlopen(url) as resp:
            _write_bytes(dest, resp.read())


# ---------------------------------------------------------------------------
# SQL helpers (for generating golden_output.csv)
# ---------------------------------------------------------------------------

def _execute_sql_readonly(db_path: str, query: str) -> tuple[str | None, pd.DataFrame | None]:
    if not query or not query.strip():
        return "Error: empty query", None
    try:
        with sqlite3.connect(f"file:{db_path}?mode=ro", uri=True) as conn:
            start = time.time()

            def _progress():
                if time.time() - start > MAX_QUERY_EXECUTION_TIMEOUT:
                    return 1

            conn.set_progress_handler(_progress, 1000)
            cursor = conn.cursor()
            try:
                cursor.execute(query)
                if cursor.description is not None:
                    columns = [desc[0] for desc in cursor.description]
                    return None, pd.DataFrame(cursor.fetchall(), columns=columns)
                return "Error: non-SELECT query", None
            except Exception as e:
                return f"Error: {e}", None
            finally:
                conn.set_progress_handler(None, 0)
    except Exception as e:
        return f"Error: {e}", None


# ---------------------------------------------------------------------------
# Blocker registry normalisation (mirrors run_hil_bench.py logic)
# ---------------------------------------------------------------------------

def _normalize_blocker_registry(raw: Any) -> dict[str, Any]:
    if isinstance(raw, dict) and "blockers" in raw:
        return raw
    if isinstance(raw, list):
        return {"blockers": raw}
    if isinstance(raw, str):
        try:
            parsed = json.loads(raw)
            return _normalize_blocker_registry(parsed)
        except (json.JSONDecodeError, ValueError):
            pass
    raise ValueError(f"Unsupported blocker_registry format: {type(raw)}")


def _ensure_strings(value: Any) -> list[str]:
    if isinstance(value, str):
        try:
            parsed = json.loads(value)
            if isinstance(parsed, list):
                return [str(v) for v in parsed]
        except (json.JSONDecodeError, ValueError):
            pass
        return [value] if value else []
    if isinstance(value, list):
        return [str(v) for v in value]
    return []


# ---------------------------------------------------------------------------
# HF dataset loading + row lookup
# ---------------------------------------------------------------------------

_hf_by_uid: dict[str, dict] | None = None


def _load_hf_sql_rows() -> dict[str, dict]:
    """Return a dict mapping uid → HF row for all SQL tasks (cached)."""
    global _hf_by_uid
    if _hf_by_uid is not None:
        return _hf_by_uid
    try:
        from datasets import load_dataset
    except ImportError:
        raise ImportError("Install 'datasets' to use the HF-based generator: pip install datasets")
    logger.info("Loading HF dataset %s …", HF_DATASET)
    ds = load_dataset(HF_DATASET, split="train")
    _hf_by_uid = {
        str(row["uid"]): dict(row)
        for row in ds
        if row.get("task_type") == "sql"
    }
    logger.info("Loaded %d SQL rows from HF dataset", len(_hf_by_uid))
    return _hf_by_uid


# ---------------------------------------------------------------------------
# Per-task artifact preparation
# ---------------------------------------------------------------------------

def _prepare_task_artifacts(
    *,
    output_dir: Path,
    dataset_name: str,
    csv_index: int | None,
    task_id: str,
    attempt_id: str,
    hf_task_id: str | None,
) -> dict[str, Any]:
    hf_rows = _load_hf_sql_rows()
    if attempt_id not in hf_rows:
        raise KeyError(
            f"attempt_id={attempt_id} not found in HF dataset "
            f"(checked {len(hf_rows)} SQL rows by uid field)"
        )
    row = hf_rows[attempt_id]

    database_name = str(row["repo_or_db_name"])
    question = str(row["problem"])
    ground_truth_sql = str(row["ground_truth_answer"])
    business_info = _ensure_strings(row.get("business_info") or [])
    blocker_registry_raw = _normalize_blocker_registry(row.get("blocker_registry") or {"blockers": []})
    blockers: list[dict[str, Any]] = blocker_registry_raw.get("blockers", [])

    # Validate blockers
    for b in blockers:
        if not b.get("description") or not b.get("resolution"):
            raise ValueError(f"Malformed blocker in {attempt_id}: {b}")
        # Normalise type from list → str if needed (matches fix_harbor_tasks.py group6)
        if isinstance(b.get("type"), list):
            b["type"] = b["type"][0] if b["type"] else None

    task_attempt_id = f"{task_id}_{attempt_id}"
    dataset_dir = output_dir / dataset_name
    shared_dir = dataset_dir / "shared"
    data_dir = shared_dir / "data"
    desc_dir = data_dir / "database_description"
    ask_human_data_dir = shared_dir / "ask-human-data"

    # Download SQLite database
    db_url = str(row["repo_or_db_download_link"])
    db_path = data_dir / "database.sqlite"
    _download(db_url, db_path)

    # Download schema CSVs
    desc_links = _ensure_strings(row.get("schema_descriptions_download_links") or [])
    for link in desc_links:
        filename = Path(link).name or "table_descriptions.csv"
        _download(link, desc_dir / filename)

    table_desc_path = desc_dir / "table_descriptions.csv"
    if not table_desc_path.exists():
        raise FileNotFoundError(f"table_descriptions.csv not found for {dataset_name}")

    # Write data_archive.json — records HF artifact URLs so warmup_data.sh can
    # re-download database.sqlite and description CSVs on a fresh machine without
    # re-running the full generator.  Only written when all artifact URLs use the
    # hf://buckets/<org>/<repo>/<path> scheme; silently skipped otherwise so that
    # the generator continues to work with plain HTTPS source URLs.
    _HF_BUCKETS_PREFIX = "hf://buckets/"

    def _hf_rel(hf_url: str) -> str | None:
        """Return '<org>/<repo>/<path>' for an hf://buckets/ URL, else None."""
        if not hf_url.startswith(_HF_BUCKETS_PREFIX):
            return None
        return hf_url[len(_HF_BUCKETS_PREFIX):]

    db_rel = _hf_rel(db_url)
    if db_rel is not None:
        hf_bucket = "/".join(db_rel.split("/")[:2])  # org/repo
        db_artifact_path = "/".join(db_rel.split("/")[2:])
        desc_artifact_paths = []
        for link in desc_links:
            rel = _hf_rel(link)
            if rel is not None:
                desc_artifact_paths.append("/".join(rel.split("/")[2:]))
        data_archive = {
            "hf_bucket": hf_bucket,
            "db_artifact_path": db_artifact_path,
            "desc_artifact_paths": desc_artifact_paths,
        }
        _write(shared_dir / "data_archive.json", json.dumps(data_archive, indent=2))

    # Write business_info.json
    business_info_data = {"database_name": database_name, "business_info": business_info}
    _write(data_dir / "business_info.json", json.dumps(business_info_data, indent=2))

    # Write blocker_registry.json
    blocker_registry_normalised = {"blockers": blockers}
    _write(
        ask_human_data_dir / "blocker_registry.json",
        json.dumps(blocker_registry_normalised, indent=2),
    )

    # Write ground_truth.sql to shared/
    _write(shared_dir / "ground_truth.sql", ground_truth_sql)

    # Generate golden_output.csv by executing ground truth SQL
    gt_err, gt_df = _execute_sql_readonly(str(db_path), ground_truth_sql)
    if gt_df is None:
        raise ValueError(f"Ground truth SQL failed for {dataset_name}: {gt_err}")
    golden_output_csv = gt_df.to_csv(index=False)
    _write(shared_dir / "golden_output.csv", golden_output_csv)

    # Write metadata.json
    metadata = {
        "csv_index": csv_index,
        "dataset_name": dataset_name,
        "hf_task_id": hf_task_id or str(row.get("task_id", "")),
        "task_id": task_id,
        "attempt_id": attempt_id,
        "task_attempt_id": task_attempt_id,
        "database_name": database_name,
        "num_blockers": len(blockers),
    }
    _write(shared_dir / "metadata.json", json.dumps(metadata, indent=2))

    return {
        "dataset_dir": dataset_dir,
        "database_name": database_name,
        "question": question,
        "blockers": blockers,
        "task_attempt_id": task_attempt_id,
        "ground_truth_sql": ground_truth_sql,
        "golden_output": golden_output_csv,
        "db_path": db_path,
    }


# ---------------------------------------------------------------------------
# Mode directory generation
# ---------------------------------------------------------------------------

def _populate_mode_dirs(payload: dict[str, Any]) -> None:
    dataset_dir: Path = payload["dataset_dir"]
    for mode in MODES:
        mode_dir = dataset_dir / mode
        env_dir = mode_dir / "environment"
        tests_dir = mode_dir / "tests"
        solution_dir = mode_dir / "solution"
        env_dir.mkdir(parents=True, exist_ok=True)
        tests_dir.mkdir(parents=True, exist_ok=True)
        solution_dir.mkdir(parents=True, exist_ok=True)

        _write(
            mode_dir / "instruction.md",
            _instruction_content(
                mode,
                payload["database_name"],
                payload["question"],
                payload["blockers"],
            ),
        )
        _write(
            mode_dir / "task.toml",
            _task_toml_content(mode, payload["database_name"], payload["task_attempt_id"]),
        )
        _write(env_dir / "Dockerfile", _DOCKERFILE)
        # Copy the MCP helper and tool-wrapper scripts into the environment dir (needed by Dockerfile COPY)
        for template_name in ("mcp.py", "setup_tools.py"):
            src = HARBOR_SQL_ROOT / "templates" / template_name
            if src.exists():
                _write_bytes(env_dir / template_name, src.read_bytes())
            else:
                logger.warning("%s template not found at %s; skipping", template_name, src)
        compose = _COMPOSE_ASK_HUMAN if mode == "ask_human" else _COMPOSE_NO_ASK_HUMAN
        _write(env_dir / "docker-compose.yaml", compose)

        _write(solution_dir / "solve.sh", _SOLVE_SH)
        _write(solution_dir / "ground_truth.sql", payload["ground_truth_sql"])

        _write(tests_dir / "test.sh", _TEST_SH)
        _write(tests_dir / "test_verify.py", _get_test_verify_py())
        _write(tests_dir / "ground_truth.sql", payload["ground_truth_sql"])
        _write(tests_dir / "golden_output.csv", payload["golden_output"])

        for script in (solution_dir / "solve.sh", tests_dir / "test.sh"):
            script.chmod(script.stat().st_mode | 0o111)


# ---------------------------------------------------------------------------
# Self-check (validate golden output matches ground truth SQL on the DB)
# ---------------------------------------------------------------------------

def _self_check(payload: dict[str, Any]) -> None:
    dataset_dir: Path = payload["dataset_dir"]
    expected = [
        dataset_dir / "shared" / "data" / "database.sqlite",
        dataset_dir / "shared" / "data" / "business_info.json",
        dataset_dir / "shared" / "data" / "database_description" / "table_descriptions.csv",
        dataset_dir / "shared" / "ask-human-data" / "blocker_registry.json",
        dataset_dir / "shared" / "ground_truth.sql",
        dataset_dir / "shared" / "golden_output.csv",
    ]
    for mode in MODES:
        expected.extend([
            dataset_dir / mode / "instruction.md",
            dataset_dir / mode / "task.toml",
            dataset_dir / mode / "environment" / "Dockerfile",
            dataset_dir / mode / "environment" / "mcp.py",
            dataset_dir / mode / "environment" / "docker-compose.yaml",
            dataset_dir / mode / "tests" / "test_verify.py",
        ])
    missing = [str(p) for p in expected if not p.exists()]
    if missing:
        raise FileNotFoundError(f"Missing generated files:\n  " + "\n  ".join(missing))

    gt_query = (dataset_dir / "shared" / "ground_truth.sql").read_text()
    gt_err, gt_df = _execute_sql_readonly(str(payload["db_path"]), gt_query)
    if gt_df is None:
        raise ValueError(f"Ground truth SQL failed in self-check: {gt_err}")
    logger.info("Self-check passed: ground truth query returned %d rows", len(gt_df))


# ---------------------------------------------------------------------------
# Main
# ---------------------------------------------------------------------------

def main() -> None:
    logging.basicConfig(level=logging.INFO, format="%(asctime)s %(levelname)s %(message)s")

    parser = argparse.ArgumentParser(
        description=(
            "Generate Harbor SQL task directories from ScaleAI/hil-bench HF dataset. "
            "Reads public CSV for task_id/attempt_id ordering, matches HF rows by uid=attempt_id."
        )
    )
    parser.add_argument(
        "--indices",
        type=int,
        nargs="+",
        help="0-based row indices in the public CSV to generate (e.g. --indices 0 3 7).",
    )
    parser.add_argument(
        "--attempt-ids",
        nargs="+",
        help="Generate specific tasks by attempt_id (bypasses --indices/--all).",
    )
    parser.add_argument("--all", action="store_true", help="Generate all 100 public tasks.")
    parser.add_argument(
        "--overwrite",
        action="store_true",
        help="Delete and regenerate existing output directories.",
    )
    parser.add_argument(
        "--no-self-check",
        action="store_true",
        help="Skip post-generation self-check.",
    )
    parser.add_argument(
        "--output-dir",
        type=Path,
        default=DEFAULT_OUTPUT_DIR,
        help=f"Output root directory (default: {DEFAULT_OUTPUT_DIR}).",
    )
    parser.add_argument(
        "--csv-path",
        type=Path,
        default=CSV_PATH,
        help=f"Path to public CSV (default: {CSV_PATH}).",
    )
    args = parser.parse_args()

    csv_path = args.csv_path.resolve()
    if not csv_path.exists():
        print(f"ERROR: CSV not found: {csv_path}", file=sys.stderr)
        sys.exit(1)

    df = pd.read_csv(csv_path)
    attempt_to_csv: dict[str, tuple[int, str, str]] = {
        str(row["attempt_id"]): (idx, str(row["task_id"]), str(row.get("repo_or_db_name", "")))
        for idx, row in df.iterrows()
    }

    # Load HF dataset once (to build uid→hf_task_id mapping)
    hf_rows = _load_hf_sql_rows()
    uid_to_hf_task_id = {uid: str(r.get("task_id", "")) for uid, r in hf_rows.items()}

    # Resolve targets
    targets: list[dict[str, Any]] = []
    if args.attempt_ids:
        for attempt_id in args.attempt_ids:
            if attempt_id in attempt_to_csv:
                csv_index, task_id, _ = attempt_to_csv[attempt_id]
                dataset_name = f"sql_{csv_index}"
            else:
                csv_index, task_id = None, "unknown"
                dataset_name = f"attempt_{attempt_id}"
            targets.append({
                "csv_index": csv_index,
                "task_id": task_id,
                "attempt_id": attempt_id,
                "dataset_name": dataset_name,
                "hf_task_id": uid_to_hf_task_id.get(attempt_id),
            })
    elif args.all:
        for idx, row in df.iterrows():
            attempt_id = str(row["attempt_id"])
            targets.append({
                "csv_index": idx,
                "task_id": str(row["task_id"]),
                "attempt_id": attempt_id,
                "dataset_name": f"sql_{idx}",
                "hf_task_id": uid_to_hf_task_id.get(attempt_id),
            })
    elif args.indices:
        for idx in args.indices:
            if idx < 0 or idx >= len(df):
                print(f"ERROR: index {idx} out of range (CSV has {len(df)} rows)", file=sys.stderr)
                sys.exit(1)
            row = df.iloc[idx]
            attempt_id = str(row["attempt_id"])
            targets.append({
                "csv_index": idx,
                "task_id": str(row["task_id"]),
                "attempt_id": attempt_id,
                "dataset_name": f"sql_{idx}",
                "hf_task_id": uid_to_hf_task_id.get(attempt_id),
            })
    else:
        parser.error("Provide --indices, --attempt-ids, or --all")

    output_dir = args.output_dir.resolve()
    output_dir.mkdir(parents=True, exist_ok=True)

    if args.overwrite:
        for t in targets:
            task_dir = output_dir / t["dataset_name"]
            if task_dir.exists():
                shutil.rmtree(task_dir)
                logger.info("Removed existing %s", task_dir)

    generated: list[str] = []
    errors: list[dict[str, Any]] = []

    for target in targets:
        attempt_id = target["attempt_id"]
        dataset_name = target["dataset_name"]
        stage = "init"
        try:
            logger.info(
                "Generating %s (attempt_id=%s, hf_task_id=%s)",
                dataset_name,
                attempt_id,
                target["hf_task_id"],
            )
            stage = "prepare_task_artifacts"
            payload = _prepare_task_artifacts(
                output_dir=output_dir,
                dataset_name=dataset_name,
                csv_index=target["csv_index"],
                task_id=target["task_id"],
                attempt_id=attempt_id,
                hf_task_id=target["hf_task_id"],
            )
            stage = "populate_mode_dirs"
            _populate_mode_dirs(payload)
            if not args.no_self_check:
                stage = "self_check"
                _self_check(payload)
            stage = "complete"
            generated.append(dataset_name)
            print(f"[ok] generated {output_dir / dataset_name}")
        except Exception as e:
            tb = traceback.format_exc()
            logger.error("Failed %s (stage=%s): %s", dataset_name, stage, e)
            errors.append({
                "dataset_name": dataset_name,
                "attempt_id": attempt_id,
                "stage": stage,
                "error": str(e),
                "traceback": tb,
            })

    print(f"\nOutput dir: {output_dir}")
    print(f"Generated:  {', '.join(generated) if generated else '(none)'}")
    if errors:
        errors_path = output_dir / "conversion_errors.json"
        errors_path.write_text(json.dumps(errors, indent=2))
        print(f"Errors ({len(errors)}): {errors_path}")
        sys.exit(1)


def _get_test_verify_py() -> str:
    """Load test_verify.py template from harbor_sql/templates/."""
    template_path = HARBOR_SQL_ROOT / "templates" / "test_verify.py"
    if template_path.exists():
        return template_path.read_text()
    raise FileNotFoundError(
        f"test_verify.py template not found at {template_path}. "
        "Expected under harbor_sql/templates/test_verify.py."
    )


if __name__ == "__main__":
    main()
