from __future__ import annotations
import chromadb
from chromadb.utils.embedding_functions import SentenceTransformerEmbeddingFunction
import argparse
import copy
import json
import os
import re
import shlex
import shutil
import subprocess
import sys
import tempfile
import threading
import urllib.request
from collections import defaultdict
from concurrent.futures import ThreadPoolExecutor, as_completed
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

import pandas as pd
from datasets import load_dataset
from dotenv import load_dotenv
from tqdm import tqdm

HF_DATASET = "[REDACTED]/hil-bench"
RUN_OWNER_DIR = Path(os.getenv("HIL_BENCH_RUN_OWNER_DIR", "/tmp/hil_bench_run_owners"))
RUN_TIMEOUT_SECONDS = 21600
DOCKER_LOADED_IMAGE_RE = re.compile(r"Loaded image:\s*(\S+)")
DOCKER_LOADED_IMAGE_ID_RE = re.compile(r"Loaded image ID:\s*(\S+)")
TRAJECTORY_TIMEOUT_OBS_RE = re.compile(r"Command '\[.*\]' timed out after \d+ seconds")
TRAJECTORY_HICCUP_OBS = "can't answer (perhaps transient hiccup)"
TRAJECTORY_ENV_DIED_OBS = "Environment died unexpectedly"
TRAJECTORY_UNKNOWN_ERROR = "Exit due to unknown error"
KB_QUERY_ERROR = "Error querying knowledge base"
SQL_QUOTING_BUG_MARKERS = (
    ("get_database_info", "Error: database $"),
    ("get_table_info", "Error: table $"),
    ("get_column_info", "Error: column $"),
    ("get_business_info", "No business information found matching '$"),
)
TRAJECTORY_RERUN_OCCURRENCE_THRESHOLD_STRICT = 1
TRAJECTORY_RERUN_OCCURRENCE_THRESHOLD_LENIENT = 3
SWEAP_TEST_CMD = (
    "bash /root/run_script.sh > /tmp/stdout.log 2> /tmp/stderr.log; "
    "python /root/parser.py /tmp/stdout.log /tmp/stderr.log /tmp/output.json; "
    "python -c \"print('SWEAP_JSON_START'); print(open('/tmp/output.json').read()); print('SWEAP_JSON_END')\""
)
SWEAP_LOG_PARSER = "sweap_json"
CSV_COLUMNS = [
    "task_name",
    "model",
    "mode",
    "pass_num",
    "status",
    "resolved",
    "cost",
    "num_steps",
    "num_questions",
    "num_blockers_resolved",
    "total_num_blockers",
    "precision",
    "recall",
    "f1",
    "tokens_sent",
    "tokens_received",
    "log_dir",
    "trajectory_dir",
]

docker_load_lock = threading.Lock()


def register_run_owner() -> Path:
    RUN_OWNER_DIR.mkdir(parents=True, exist_ok=True)
    token = RUN_OWNER_DIR / f"{os.getpid()}.owner"
    token.write_text(str(os.getpid()))
    return token


def unregister_run_owner(token: Path) -> None:
    token.unlink(missing_ok=True)


def any_hil_bench_run_active() -> bool:
    if not RUN_OWNER_DIR.exists():
        return False
    for token in RUN_OWNER_DIR.glob("*.owner"):
        try:
            pid = int(token.stem)
            os.kill(pid, 0)
            return True
        except ProcessLookupError:
            token.unlink(missing_ok=True)
        except (ValueError, PermissionError):
            return True
    return False


def read_hf_uri(uri: str) -> bytes:
    from huggingface_hub import HfFileSystem

    fs = HfFileSystem()
    with fs.open(uri, "rb") as f:
        return f.read()


def download_to_path(source: str, destination: Path) -> None:
    destination.parent.mkdir(parents=True, exist_ok=True)
    if source.startswith("hf://"):
        destination.write_bytes(read_hf_uri(source))
        return
    if source.startswith("http://") or source.startswith("https://"):
        with urllib.request.urlopen(source, timeout=120) as resp:
            destination.write_bytes(resp.read())
        return
    src_path = Path(source)
    if not src_path.exists():
        raise FileNotFoundError(f"Unsupported or missing artifact source: {source}")
    shutil.copy2(src_path, destination)


def normalize_blocker_registry(raw: Any) -> dict[str, Any]:
    if raw is None:
        return {"blockers": []}
    if isinstance(raw, dict):
        return raw
    if isinstance(raw, list):
        return {"blockers": raw}
    if isinstance(raw, str):
        text = raw.strip()
        if not text:
            return {"blockers": []}
        parsed = json.loads(text)
        if isinstance(parsed, dict):
            return parsed
        if isinstance(parsed, list):
            return {"blockers": parsed}
    raise ValueError("Unsupported blocker_registry format in HF row")


def ensure_list_of_strings(value: Any) -> list[str]:
    if value is None:
        return []
    if isinstance(value, list):
        return [str(v) for v in value if str(v).strip()]
    if isinstance(value, str):
        stripped = value.strip()
        if not stripped:
            return []
        parsed = json.loads(stripped) if stripped.startswith("[") else [stripped]
        if isinstance(parsed, list):
            return [str(v) for v in parsed if str(v).strip()]
        return [str(parsed)]
    return [str(value)]


def build_chroma_db(chroma_path: Path, database_name: str, documents: list[str]) -> None:
    chroma_path.mkdir(parents=True, exist_ok=True)
    client = chromadb.PersistentClient(path=str(chroma_path))
    embedding_fn = SentenceTransformerEmbeddingFunction(model_name="all-MiniLM-L6-v2")
    collection_name = "business_info"
    try:
        client.delete_collection(collection_name)
    except Exception:
        pass
    collection = client.get_or_create_collection(
        collection_name,
        embedding_function=embedding_fn,
    )
    if documents:
        ids = [f"doc_{i}" for i in range(len(documents))]
        collection.add(
            ids=ids,
            documents=documents,
            metadatas=[{"database_name": database_name} for _ in documents],
        )


def select_task_rows(
    rows: list[dict[str, Any]],
    task_type: str,
    num_datapoints: int | None,
) -> list[dict[str, Any]]:
    filtered = [r for r in rows if r["task_type"].lower() == task_type]
    if num_datapoints is not None:
        filtered = filtered[:num_datapoints]
    return filtered


def write_blocker_registry(task_dir: Path, row: dict[str, Any]) -> Path:
    blocker_registry = normalize_blocker_registry(row.get("blocker_registry"))
    blocker_registry_path = task_dir / "blocker_registry.json"
    blocker_registry_path.write_text(json.dumps(blocker_registry, indent=2))
    return blocker_registry_path


def load_docker_image_from_archive(archive_path: Path) -> str:
    with docker_load_lock:
        if archive_path.name.endswith(".tar.zst") or archive_path.suffix == ".zst":
            cmd = (
                f"zstd -dc {shlex.quote(str(archive_path))} | docker load"
            )
            result = subprocess.run(
                cmd,
                shell=True,
                executable="/bin/bash",
                capture_output=True,
                text=True,
            )
        else:
            result = subprocess.run(
                ["docker", "load", "-i", str(archive_path)],
                capture_output=True,
                text=True,
            )
        if result.returncode != 0:
            raise RuntimeError(
                "Failed to load Docker image archive "
                f"{archive_path}: {result.stderr.strip() or result.stdout.strip()}"
            )
        combined_output = f"{result.stdout}\n{result.stderr}"
        image_matches = DOCKER_LOADED_IMAGE_RE.findall(combined_output)
        if image_matches:
            return image_matches[-1].strip()
        id_matches = DOCKER_LOADED_IMAGE_ID_RE.findall(combined_output)
        if id_matches:
            image_id = id_matches[-1].strip()
            inspect = subprocess.run(
                ["docker", "image", "inspect", image_id, "--format", "{{json .RepoTags}}"],
                capture_output=True,
                text=True,
            )
            if inspect.returncode == 0:
                try:
                    repo_tags = json.loads(inspect.stdout.strip() or "[]")
                    if isinstance(repo_tags, list):
                        for tag in repo_tags:
                            if isinstance(tag, str) and tag and tag != "<none>:<none>":
                                return tag
                except Exception:
                    pass
            return image_id
        raise ValueError(
            "Could not find loaded image name or ID in docker load output for "
            f"{archive_path}.\nOutput:\n{combined_output}"
        )


def prepare_sql_task(row: dict[str, Any], tasks_root: Path) -> tuple[str, dict[str, Any]]:
    task_id = str(row["task_id"])
    task_dir = tasks_root / task_id
    task_dir.mkdir(parents=True, exist_ok=True)

    db_name = str(row["repo_or_db_name"])
    db_path = task_dir / f"{db_name}.sqlite"
    download_to_path(str(row["repo_or_db_download_link"]), db_path)

    desc_links = ensure_list_of_strings(row.get("schema_descriptions_download_links"))
    table_desc_path = None
    for link in desc_links:
        local_path = task_dir / Path(link).name
        download_to_path(link, local_path)
        if local_path.name == "table_descriptions.csv":
            table_desc_path = local_path
    if table_desc_path is None:
        raise FileNotFoundError(f"{task_id} is missing table_descriptions.csv")

    blocker_registry_path = write_blocker_registry(task_dir, row)
    business_info = ensure_list_of_strings(row.get("business_info"))
    chroma_path = task_dir / "chroma_db"
    build_chroma_db(chroma_path, db_name, business_info)

    instance = {
        "env": {
            "database_type": "sqlite",
            "name": "main",
            "max_rows": 200,
            "database_name": db_name,
            "base_db_path": str(db_path.resolve()),
            "working_db_path": "",
            "diff_queries": [],
            "chroma_path": str(chroma_path.resolve()),
        },
        "problem_statement": {
            "type": "sql",
            "id": task_id,
            "question": str(row["problem"]),
            "ground_truth_query": str(row["ground_truth_answer"]),
            "business_info": business_info,
            "database_name": db_name,
            "extra_fields": {},
            "expected_sorted": False,
            "required_unique": False,
            "no_extra_columns_allowed": False,
            "blocker_registry_path": str(blocker_registry_path.resolve()),
            "table_descriptions_path": str(table_desc_path.resolve()),
        },
    }
    return task_id, instance


def prepare_swe_task(
    row: dict[str, Any],
    tasks_root: Path,
    loaded_image_cache: dict[str, str],
) -> tuple[str, dict[str, Any]]:
    task_id = str(row["task_id"])
    uid = str(row.get("uid", "")).strip()
    if not uid:
        raise ValueError(f"SWE row {task_id} missing uid")
    task_dir = tasks_root / task_id
    task_dir.mkdir(parents=True, exist_ok=True)

    image_link = str(row["repo_or_db_download_link"])
    image_name: str
    if image_link in loaded_image_cache:
        image_name = loaded_image_cache[image_link]
    else:
        archive_name = Path(image_link).name or f"{uid}.tar.zst"
        archive_path = task_dir / archive_name
        download_to_path(image_link, archive_path)
        image_name = load_docker_image_from_archive(archive_path)
        loaded_image_cache[image_link] = image_name

    blocker_registry_path = write_blocker_registry(task_dir, row)
    (task_dir / "problem_statement.txt").write_text(str(row["problem"]))

    for script_name in ("run_script.sh", "parser.py"):
        dest = task_dir / script_name
        if not dest.exists():
            try:
                result = subprocess.run(
                    [
                        "docker",
                        "run",
                        "--rm",
                        "--entrypoint",
                        "",
                        image_name,
                        "cat",
                        f"/root/{script_name}",
                    ],
                    capture_output=True,
                    text=True,
                    check=False,
                )
                if result.returncode == 0 and result.stdout:
                    dest.write_text(result.stdout)
            except Exception:
                pass

    tests_to_pass = ensure_list_of_strings(row.get("tests_to_pass"))
    test_files = ensure_list_of_strings(row.get("test_files"))
    test_patch = str(row.get("test_patch") or "")
    metadata = {
        "instance_id": task_id,
        "repo_name": "app",
        "base_commit": "HEAD",
        "image_name": image_name,
        "log_parser": SWEAP_LOG_PARSER,
        "test_cmd": SWEAP_TEST_CMD,
        "test_patch": test_patch,
        "swe_bench_metadata": {
            "FAIL_TO_PASS": tests_to_pass,
            "PASS_TO_PASS": [],
        },
        "test_files": test_files,
        "uid": uid,
        "repo_or_db_name": str(row.get("repo_or_db_name", "")),
    }
    (task_dir / "metadata.json").write_text(json.dumps(metadata, indent=2))

    instance = {
        "instance_id": task_id,
        "problem_statement": str(row["problem"]),
        "repo_name": "app",
        "base_commit": "HEAD",
        "image_name": image_name,
        "extra_fields": {
            "uid": uid,
            "repo_or_db_name": str(row.get("repo_or_db_name", "")),
            "ground_truth_patch": str(row.get("ground_truth_answer", "")),
            "blocker_registry_path": str(blocker_registry_path.resolve()),
        },
    }
    return task_id, instance


def cleanup_swe_containers_for_image(image_name: str) -> int:
    candidate_ids: set[str] = set()
    try:
        result = subprocess.run(
            [
                "docker",
                "ps",
                "-a",
                "--format",
                "{{.ID}}\t{{.Status}}",
                "--filter",
                f"ancestor={image_name}",
            ],
            capture_output=True,
            text=True,
            check=False,
        )
        active_owner_exists = any_hil_bench_run_active()
        for line in result.stdout.splitlines():
            parts = line.split("\t")
            if len(parts) < 2:
                continue
            container_id = parts[0].strip()
            status = parts[1].lower()
            if status.startswith("exited") or status.startswith("created"):
                candidate_ids.add(container_id)
                continue
            if status.startswith("up") and not active_owner_exists:
                candidate_ids.add(container_id)
        if not candidate_ids:
            return 0
        subprocess.run(
            ["docker", "rm", "-f", *sorted(candidate_ids)],
            stdout=subprocess.DEVNULL,
            stderr=subprocess.DEVNULL,
            check=False,
        )
        return len(candidate_ids)
    except Exception:
        return 0


def build_runtime_workspace(
    task_type: str,
    workspace_dir: Path,
    rows: list[dict[str, Any]],
    num_datapoints: int | None,
    models: list[str],
    num_concurrent_datapoints: int,
) -> tuple[Path, Path, list[str], dict[str, str]]:
    selected = select_task_rows(rows, task_type=task_type, num_datapoints=num_datapoints)
    if not selected:
        raise ValueError(f"No {task_type.upper()} tasks found for selected filters.")

    tasks_root = workspace_dir / f"{task_type}_tasks"
    tasks_root.mkdir(parents=True, exist_ok=True)
    task_names = [str(row["task_id"]) for row in selected]
    task_to_instance = {}
    task_to_image = {}
    loaded_image_cache = {}

    total_units = len(selected) * len(models)
    print(
        f"📊 Preparing {len(selected)} {task_type.upper()} datapoints x {len(models)} models = "
        f"{total_units} (attempt, model) units"
    )
    with tqdm(total=total_units, desc=f"Preparing {task_type}", unit="attempt-model") as pbar:
        with ThreadPoolExecutor(max_workers=max(1, num_concurrent_datapoints)) as executor:
            futures = {}
            for row in selected:
                if task_type == "sql":
                    future = executor.submit(prepare_sql_task, row, tasks_root)
                else:
                    future = executor.submit(prepare_swe_task, row, tasks_root, loaded_image_cache)
                futures[future] = str(row["task_id"])

            for future in as_completed(futures):
                task_id = futures[future]
                prepared_task_id, instance = future.result()
                task_to_instance[prepared_task_id] = instance
                image_name = str(instance.get("image_name") or "").strip()
                if image_name:
                    task_to_image[prepared_task_id] = image_name
                if prepared_task_id != task_id:
                    raise ValueError(f"Task mismatch during preparation: {prepared_task_id} vs {task_id}")
                pbar.update(len(models))

    instances = [task_to_instance[name] for name in task_names]
    instances_path = tasks_root / "instances.json"
    instances_path.write_text(json.dumps(instances, indent=2))
    return instances_path, tasks_root, task_names, task_to_image


def run_hil_cli(
    task_type: str,
    args: argparse.Namespace,
    instances_path: Path,
    run_name: str,
) -> tuple[int, Path]:
    output_dir = args.output_dir.resolve()
    cmd = [
        sys.executable,
        "-m",
        "hil_bench.cli",
        task_type,
        str(instances_path),
        "--model",
        *args.models,
        "--passes",
        str(args.passes),
        "--config-mapping",
        str(args.agent_config_mapping.resolve()),
        "--run-name",
        run_name,
        "--num-workers",
        str(args.num_workers),
        "--per-instance-cost-limit",
        str(args.per_instance_cost_limit),
        "--output-dir",
        str(output_dir),
    ]
    if args.modes == ["baseline", "ask_human", "full_info"]:
        cmd.append("--all-modes")
    else:
        if "ask_human" in args.modes:
            cmd.append("--ask-human")
        if "full_info" in args.modes:
            cmd.append("--full-info")
    cmd.extend(["--judge-config", str(args.judge_config.resolve())])
    if args.max_steps is not None:
        cmd.extend(["--max-steps", str(args.max_steps)])
    if not args.cleanup_docker:
        cmd.append("--no-cleanup-docker")

    print(f"\n🚀 Running {task_type.upper()} batch:")
    print(" ".join(cmd))
    try:
        result = subprocess.run(cmd, timeout=RUN_TIMEOUT_SECONDS)
    except subprocess.TimeoutExpired:
        print(f"❌ {task_type.upper()} run timed out after {RUN_TIMEOUT_SECONDS} seconds")
        return 124, output_dir / run_name
    run_dir = output_dir / run_name
    if not run_dir.exists():
        candidates = sorted(output_dir.glob(f"{run_name}*"), key=lambda p: p.stat().st_mtime)
        if candidates:
            run_dir = candidates[-1]
    return result.returncode, run_dir


def compute_hil_metrics(logs: dict[str, dict[str, Any]]) -> dict[str, Any]:
    total_questions = 0
    total_blockers_present = 0
    total_blockers_discovered = 0
    for log_data in logs.values():
        n_blockers = int(log_data.get("n_blockers", 0))
        questions = log_data.get("questions") or log_data.get("entries") or []
        discovered = len({q.get("blocker_name") for q in questions if q.get("blocker_name")})
        n_questions = len(questions)
        precision = discovered / n_questions if n_questions > 0 else 0.0
        recall = discovered / n_blockers if n_blockers > 0 else 0.0
        ask_f1 = 2 * precision * recall / (precision + recall) if (precision + recall) > 0 else 0.0
        log_data["precision"] = precision
        log_data["recall"] = recall
        log_data["ask_f1"] = ask_f1
        total_questions += n_questions
        total_blockers_present += n_blockers
        total_blockers_discovered += discovered
    return {
        "instances": logs,
        "precision": total_blockers_discovered / total_questions if total_questions > 0 else 0.0,
        "recall": (
            total_blockers_discovered / total_blockers_present if total_blockers_present > 0 else 0.0
        ),
    }


def extract_traj_stats(traj_path: Path) -> dict[str, Any]:
    if not traj_path.exists():
        return {}
    try:
        data = json.loads(traj_path.read_text())
    except Exception:
        return {}
    model_stats = data.get("info", {}).get("model_stats", {})
    steps = data.get("trajectory", [])
    num_questions = None
    if isinstance(steps, list):
        num_questions = 0
        for step in steps:
            if not isinstance(step, dict):
                continue
            action = step.get("action", "")
            if isinstance(action, str) and action.lstrip().startswith("ask_human "):
                num_questions += 1
    return {
        "tokens_sent": model_stats.get("tokens_sent", model_stats.get("input_tokens")),
        "tokens_received": model_stats.get("tokens_received", model_stats.get("output_tokens")),
        "num_steps": len(steps) if isinstance(steps, list) else None,
        "num_questions": num_questions,
        "cost": model_stats.get("instance_cost"),
    }


def parse_metrics_rows(
    task_type: str,
    results_dir: Path,
    expected_passes: int,
    log_dir: str | None,
) -> list[dict[str, Any]]:
    rows = []
    model_dirs = [p for p in results_dir.iterdir() if p.is_dir() and p.name != "metadata"]
    for model_dir in model_dirs:
        mode_dirs = [p for p in model_dir.iterdir() if p.is_dir()]
        for mode_dir in mode_dirs:
            mode = mode_dir.name
            pass_dirs = [mode_dir]
            if (mode_dir / "pass_1").exists():
                pass_dirs = sorted(
                    [p for p in mode_dir.iterdir() if p.is_dir() and p.name.startswith("pass_")]
                )

            for pass_dir in pass_dirs:
                pass_num = int(pass_dir.name.replace("pass_", "")) if pass_dir.name.startswith("pass_") else 1
                metrics_file = pass_dir / "metrics.json"
                preds_file = pass_dir / "preds.json"
                if not (metrics_file.exists() and preds_file.exists()):
                    continue

                metrics = json.loads(metrics_file.read_text())
                preds = json.loads(preds_file.read_text())
                ask_logs_file = pass_dir / "ask_human_logs.json"
                hil_by_instance = {}
                pass_hil_metrics = {}
                if ask_logs_file.exists():
                    logs = json.loads(ask_logs_file.read_text())
                    hil_by_instance = compute_hil_metrics(logs).get("instances", {})
                else:
                    pass_hil_metrics = metrics.get("hil_metrics", {}) or {}

                sql_results = metrics.get("results", {})
                swe_resolved = set(metrics.get("resolved_instances", []))
                swe_instance_metrics = metrics.get("instances", {})
                raw_eval = metrics.get("raw_eval_results", {}) or {}
                swe_eval_results = raw_eval.get("results", {}) if isinstance(raw_eval, dict) else {}
                swe_error_ids = set(raw_eval.get("error_ids", [])) if isinstance(raw_eval, dict) else set()
                for full_instance_id, pred in preds.items():
                    task_name = full_instance_id.split("__")[0]
                    model_name = model_dir.name
                    traj_path = pass_dir / full_instance_id / f"{full_instance_id}.traj"
                    traj_stats = extract_traj_stats(traj_path)

                    if task_type == "sql":
                        sql_result = sql_results.get(full_instance_id, {})
                        sql_completed = sql_result.get("completed", False)
                        resolved = sql_result.get("resolved", False) if sql_completed else None
                        patch = str(pred.get("model_patch", "")).strip()
                        if not sql_completed:
                            status = "infra_error"
                            resolved = None
                        elif resolved:
                            status = "resolved"
                        else:
                            status = "unresolved"
                        cost = sql_result.get("cost", traj_stats.get("cost"))
                        num_steps = traj_stats.get("num_steps") or sql_result.get("num_steps")
                    else:
                        eval_result = swe_eval_results.get(full_instance_id) or swe_eval_results.get(task_name) or {}
                        completed = eval_result.get("completed") if isinstance(eval_result, dict) else None
                        in_error_ids = task_name in swe_error_ids or full_instance_id in swe_error_ids
                        resolved = full_instance_id in swe_resolved
                        patch = str(pred.get("model_patch", "")).strip()
                        if in_error_ids or not completed:
                            status = "infra_error"
                            resolved = None
                        else:
                            status = "resolved" if resolved else "unresolved"
                        inst_metrics = swe_instance_metrics.get(full_instance_id, {})
                        cost = inst_metrics.get("cost", traj_stats.get("cost"))
                        num_steps = traj_stats.get("num_steps") or inst_metrics.get("num_steps")

                    h = hil_by_instance.get(full_instance_id) or {}
                    questions = h.get("questions") or h.get("entries") or []
                    n_questions = traj_stats.get("num_questions")
                    if n_questions is None:
                        n_questions = len(questions)
                    n_blockers = h.get("n_blockers")
                    n_blockers_discovered = len(
                        {q.get("blocker_name") for q in questions if q.get("blocker_name")}
                    )
                    if n_questions is None and not h and pass_hil_metrics:
                        # When no per-instance logs file is emitted (e.g., ask_human mode with zero questions),
                        # batch_runner stores only pass-level zero HIL metrics in metrics.json.
                        n_questions = pass_hil_metrics.get("n_questions")
                        n_blockers = pass_hil_metrics.get("n_blockers_present")
                        discovered = pass_hil_metrics.get("n_blockers_discovered", 0)
                        n_blockers_discovered = int(discovered) if discovered is not None else 0
                    row = {
                        "task_type": task_type,
                        "task_name": task_name,
                        "model": model_name,
                        "mode": mode,
                        "pass_num": pass_num,
                        "status": status,
                        "resolved": resolved,
                        "cost": cost,
                        "num_steps": num_steps,
                        "num_questions": n_questions if n_questions is not None else None,
                        "num_blockers_resolved": (
                            n_blockers_discovered
                            if (n_questions is not None or n_blockers is not None)
                            else None
                        ),
                        "total_num_blockers": n_blockers,
                        "precision": h.get("precision", pass_hil_metrics.get("precision")),
                        "recall": h.get("recall", pass_hil_metrics.get("recall")),
                        "f1": h.get("ask_f1", pass_hil_metrics.get("ask_f1")),
                        "tokens_sent": traj_stats.get("tokens_sent"),
                        "tokens_received": traj_stats.get("tokens_received"),
                        "log_dir": log_dir,
                        "trajectory_dir": str((pass_dir / full_instance_id).resolve()),
                    }
                    rows.append(row)

    by_key = defaultdict(dict)
    for row in rows:
        by_key[(row["task_type"], row["task_name"], row["model"], row["mode"])][int(row["pass_num"])] = row
    padded_rows = []
    for key, pass_map in by_key.items():
        row_task_type, task_name, model, mode = key
        for pass_num in range(1, expected_passes + 1):
            if pass_num in pass_map:
                padded_rows.append(pass_map[pass_num])
                continue
            padded_rows.append(
                {
                    "task_type": row_task_type,
                    "task_name": task_name,
                    "model": model,
                    "mode": mode,
                    "pass_num": pass_num,
                    "status": "infra_error",
                    "resolved": None,
                    "cost": None,
                    "num_steps": None,
                    "num_questions": None,
                    "num_blockers_resolved": None,
                    "total_num_blockers": None,
                    "precision": None,
                    "recall": None,
                    "f1": None,
                    "tokens_sent": None,
                    "tokens_received": None,
                    "log_dir": log_dir,
                    "trajectory_dir": str((results_dir / model / mode).resolve()),
                }
            )
    return sorted(
        padded_rows,
        key=lambda r: (r["task_type"], r["task_name"], r["model"], r["mode"], r["pass_num"]),
    )


def write_pass_csv(rows: list[dict[str, Any]], csv_path: Path) -> None:
    csv_path.parent.mkdir(parents=True, exist_ok=True)
    df = pd.DataFrame(rows)
    for col in CSV_COLUMNS:
        if col not in df.columns:
            df[col] = None
    df = df[CSV_COLUMNS]
    df.to_csv(csv_path, index=False)


def safe_mean(values: list[float | int | None]) -> float | None:
    valid = [float(v) for v in values if v is not None]
    if not valid:
        return None
    return sum(valid) / len(valid)


def summarize_rows(
    rows: list[dict[str, Any]],
    include_partial: bool,
    expected_passes: int,
) -> dict[str, dict[str, dict[str, Any]]]:
    grouped_attempt_rows = defaultdict(list)
    for row in rows:
        grouped_attempt_rows[(row["task_name"], row["model"], row["mode"])].append(row)
    grouped_mode_model_attempts = defaultdict(list)
    for (task_name, model, mode), attempt_rows in grouped_attempt_rows.items():
        trajectory_cache: dict[str, list[dict[str, str]]] = {}
        valid_passes = []
        for row in sorted(attempt_rows, key=lambda r: int(r.get("pass_num", 0))):
            if row.get("status") == "infra_error":
                continue
            trajectory_dir = str(row.get("trajectory_dir") or "")
            if trajectory_dir not in trajectory_cache:
                trajectory_cache[trajectory_dir] = load_trajectory_steps_from_dir(trajectory_dir)
            if trajectory_needs_rerun(trajectory_cache[trajectory_dir]):
                continue
            valid_passes.append(row)
        num_valid = len(valid_passes)
        should_include = num_valid >= 1 if include_partial else num_valid >= expected_passes
        if not should_include:
            continue
        grouped_mode_model_attempts[(mode, model)].append(valid_passes)

    finalized: dict[str, dict[str, dict[str, Any]]] = defaultdict(dict)
    for (mode, model), attempt_passes in grouped_mode_model_attempts.items():
        num_solved_by_pass_k = {k: 0 for k in range(1, expected_passes + 1)}
        num_attempts_with_k_passes = {k: 0 for k in range(1, expected_passes + 1)}
        total_attempts_and_passes = 0
        total_cost = 0.0
        total_steps = 0.0
        total_tokens_sent = 0.0
        total_tokens_received = 0.0
        total_questions = 0.0
        total_blockers_resolved = 0.0
        total_blockers_present = 0.0
        for valid_passes in attempt_passes:
            num_valid = len(valid_passes)
            for k in range(1, expected_passes + 1):
                if num_valid >= k:
                    num_attempts_with_k_passes[k] += 1
            for k in range(1, num_valid + 1):
                if any(bool(valid_passes[i].get("resolved")) for i in range(k)):
                    num_solved_by_pass_k[k] += 1
            for row in valid_passes:
                total_attempts_and_passes += 1
                total_cost += float(row.get("cost") or 0.0)
                total_steps += float(row.get("num_steps") or 0.0)
                total_tokens_sent += float(row.get("tokens_sent") or 0.0)
                total_tokens_received += float(row.get("tokens_received") or 0.0)
                total_questions += float(row.get("num_questions") or 0.0)
                if mode == "ask_human":
                    total_blockers_resolved += float(row.get("num_blockers_resolved") or 0.0)
                    total_blockers_present += float(row.get("total_num_blockers") or 0.0)

        metrics: dict[str, Any] = {
            "num_included_attempts": len(attempt_passes),
            "num_passes": expected_passes,
            "total_attempts_and_passes": total_attempts_and_passes,
            "avg_cost_per_pass": (total_cost / total_attempts_and_passes) if total_attempts_and_passes > 0 else 0.0,
            "avg_steps_per_pass": (total_steps / total_attempts_and_passes) if total_attempts_and_passes > 0 else 0.0,
            "avg_tokens_sent_per_pass": (
                total_tokens_sent / total_attempts_and_passes if total_attempts_and_passes > 0 else 0.0
            ),
            "avg_tokens_received_per_pass": (
                total_tokens_received / total_attempts_and_passes if total_attempts_and_passes > 0 else 0.0
            ),
            "avg_tokens_total_per_pass": (
                (total_tokens_sent + total_tokens_received) / total_attempts_and_passes
                if total_attempts_and_passes > 0
                else 0.0
            ),
        }
        for k in range(1, expected_passes + 1):
            denominator = num_attempts_with_k_passes[k]
            metrics[f"pass_at_{k}"] = num_solved_by_pass_k[k] / denominator if denominator > 0 else 0.0
            metrics[f"pass_at_{k}_n"] = denominator
        if mode == "ask_human":
            ask_precision = total_blockers_resolved / total_questions if total_questions > 0 else 0.0
            ask_recall = (
                total_blockers_resolved / total_blockers_present if total_blockers_present > 0 else 0.0
            )
            ask_f1 = (
                2 * ask_precision * ask_recall / (ask_precision + ask_recall)
                if (ask_precision + ask_recall) > 0
                else 0.0
            )
            metrics["ask_precision"] = ask_precision
            metrics["ask_recall"] = ask_recall
            metrics["ask_f1"] = ask_f1
            metrics["avg_num_questions_per_pass"] = (
                total_questions / total_attempts_and_passes if total_attempts_and_passes > 0 else 0.0
            )
        finalized[mode][model] = metrics
    return dict(finalized)


def build_summary(rows: list[dict[str, Any]], include_partial: bool, expected_passes: int) -> dict[str, Any]:
    sql_rows = [r for r in rows if r.get("task_type") == "sql"]
    swe_rows = [r for r in rows if r.get("task_type") == "swe"]
    both_rows = list(rows)
    return {
        "metadata": {
            "include_partial": include_partial,
            "num_passes": expected_passes,
            "generated_at": datetime.now(timezone.utc).isoformat(),
        },
        "SQL": summarize_rows(sql_rows, include_partial=include_partial, expected_passes=expected_passes),
        "SWE": summarize_rows(swe_rows, include_partial=include_partial, expected_passes=expected_passes),
        "BOTH": summarize_rows(both_rows, include_partial=include_partial, expected_passes=expected_passes),
    }


def stringify_trajectory_value(value: Any) -> str:
    if isinstance(value, str):
        return value
    try:
        return json.dumps(value, ensure_ascii=True)
    except Exception:
        return str(value)


def extract_public_trajectory_steps(traj_payload: dict[str, Any]) -> list[dict[str, str]]:
    raw_steps = traj_payload.get("trajectory", [])
    if not isinstance(raw_steps, list):
        return []
    steps: list[dict[str, str]] = []
    for step in raw_steps:
        if not isinstance(step, dict):
            continue
        step_payload: dict[str, str] = {
            "act": stringify_trajectory_value(step.get("action", "")),
            "obs": stringify_trajectory_value(step.get("observation", "")),
        }
        for key in [
            "response",
            "thought",
            "execution_time",
            "state",
            "extra_info",
            "tool_calls",
            "tool_call_ids",
            "thinking_blocks",
        ]:
            if key in step:
                value = step.get(key)
                if value is not None and value != "":
                    step_payload[key] = stringify_trajectory_value(value)
        steps.append(step_payload)
    return steps


def load_trajectory_steps_from_dir(trajectory_dir: str | None) -> list[dict[str, str]]:
    if not trajectory_dir:
        return []
    traj_dir = Path(trajectory_dir)
    if not traj_dir.exists() or not traj_dir.is_dir():
        return []
    traj_files = sorted(traj_dir.glob("*.traj"))
    if not traj_files:
        return []
    try:
        payload = json.loads(traj_files[0].read_text())
    except Exception:
        return []
    return extract_public_trajectory_steps(payload)


def trajectory_has_timeout_obs(trajectory: list[dict[str, str]]) -> bool:
    count = 0
    for step in trajectory:
        obs = step.get("obs", "")
        if isinstance(obs, str) and TRAJECTORY_TIMEOUT_OBS_RE.search(obs):
            count += 1
    return count >= TRAJECTORY_RERUN_OCCURRENCE_THRESHOLD_LENIENT


def trajectory_has_hiccup_obs(trajectory: list[dict[str, str]]) -> bool:
    count = 0
    for step in trajectory:
        obs = step.get("obs", "")
        if isinstance(obs, str) and obs.strip() == TRAJECTORY_HICCUP_OBS:
            count += 1
    return count >= TRAJECTORY_RERUN_OCCURRENCE_THRESHOLD_STRICT


def trajectory_has_env_died_obs(trajectory: list[dict[str, str]]) -> bool:
    if not trajectory:
        return False
    obs = trajectory[-1].get("obs", "")
    return isinstance(obs, str) and TRAJECTORY_ENV_DIED_OBS in obs


def trajectory_has_unknown_error(trajectory: Any) -> bool:
    """True if any trajectory step observation ended due to an unknown error"""
    if not isinstance(trajectory, list):
        return False
    last_step = trajectory[-1]
    if not isinstance(last_step, dict):
        return False
    response = last_step.get("response", "")
    if not isinstance(response, str):
        return False
    return TRAJECTORY_UNKNOWN_ERROR in response


def trajectory_has_kb_query_error(trajectory: Any) -> bool:
    """True if any trajectory step observation ended due to a knowledge base query error"""
    if not isinstance(trajectory, list) or not trajectory:
        return False
    count = 0
    for step in trajectory:
        if not isinstance(step, dict):
            continue
        obs = step.get("obs", "")
        if isinstance(obs, str) and KB_QUERY_ERROR in obs:
            count += 1
            if count >= TRAJECTORY_RERUN_OCCURRENCE_THRESHOLD_STRICT:
                return True
    return False


def trajectory_has_sql_quoting_bug_obs(trajectory: Any) -> bool:
    """True if any step shows an observation that is an artifact of the ANSI-C quoting bug."""
    if not isinstance(trajectory, list):
        return False
    for step in trajectory:
        if not isinstance(step, dict):
            continue
        act = step.get("act", "")
        obs = step.get("obs", "")
        if not isinstance(act, str) or not isinstance(obs, str):
            continue
        tool = act.split(None, 1)[0] if act.strip() else ""
        for marker_tool, marker_obs in SQL_QUOTING_BUG_MARKERS:
            if tool == marker_tool and obs.startswith(marker_obs):
                return True
    return False


def trajectory_needs_rerun(trajectory: list[dict[str, str]]) -> bool:
    return (
        trajectory_has_timeout_obs(trajectory)
        or trajectory_has_hiccup_obs(trajectory)
        or trajectory_has_env_died_obs(trajectory)
        or trajectory_has_unknown_error(trajectory)
        or trajectory_has_kb_query_error(trajectory)
        or trajectory_has_sql_quoting_bug_obs(trajectory)
    )


def _pass_needs_rerun(pass_dir: Path) -> bool:
    """True if the pass dir is missing, empty, or contains any trajectory that needs rerun."""
    if not pass_dir.exists():
        return True
    traj_files = list(pass_dir.glob("**/*.traj"))
    if not traj_files:
        return True
    for traj_file in traj_files:
        try:
            payload = json.loads(traj_file.read_text())
            steps = extract_public_trajectory_steps(payload)
            if trajectory_needs_rerun(steps):
                return True
        except Exception:
            return True
    return False


_RERUN_SKIP_DIRS = {"public_metrics", "metadata"}


def find_passes_needing_rerun(run_dir: Path, passes: int) -> dict[tuple[str, str], list[int]]:
    """Scan run_dir and return {(model_dir_name, mode_dir_name): [pass_nums_needing_rerun]}."""
    result: dict[tuple[str, str], list[int]] = {}
    if not run_dir.exists():
        return result
    for model_dir in sorted(run_dir.iterdir()):
        if not model_dir.is_dir() or model_dir.name in _RERUN_SKIP_DIRS:
            continue
        for mode_dir in sorted(model_dir.iterdir()):
            if not mode_dir.is_dir():
                continue
            bad: list[int] = []
            for pass_num in range(1, passes + 1):
                if _pass_needs_rerun(mode_dir / f"pass_{pass_num}"):
                    bad.append(pass_num)
            if bad:
                result[(model_dir.name, mode_dir.name)] = bad
    return result


def merge_rerun_results(
    original_run_dir: Path,
    temp_run_dir: Path,
    needs_rerun: dict[tuple[str, str], list[int]],
) -> None:
    """Overwrite bad pass slots in original_run_dir with matching results from temp_run_dir."""
    for (model_name, mode_name), bad_pass_nums in needs_rerun.items():
        for j, orig_pass_num in enumerate(bad_pass_nums):
            src = temp_run_dir / model_name / mode_name / f"pass_{j + 1}"
            dst = original_run_dir / model_name / mode_name / f"pass_{orig_pass_num}"
            if not src.exists():
                print(f"  ⚠️  Rerun result missing: {src} (pass {orig_pass_num} for {model_name}/{mode_name})")
                continue
            dst.parent.mkdir(parents=True, exist_ok=True)
            if dst.exists():
                shutil.rmtree(dst)
            shutil.copytree(src, dst)
            print(f"  ✅ Merged rerun pass {orig_pass_num} for {model_name}/{mode_name}")


def export_trajectories(results_dirs: list[Path], target_root: Path) -> int:
    count = 0
    for results_dir in results_dirs:
        for traj_path in results_dir.glob("**/*.traj"):
            relative_parts = traj_path.relative_to(results_dir).parts
            if len(relative_parts) < 4:
                continue
            model_safe = relative_parts[0]
            mode = relative_parts[1]
            if relative_parts[2].startswith("pass_"):
                pass_part = relative_parts[2]
                instance_part = relative_parts[3]
            else:
                pass_part = "pass_1"
                instance_part = relative_parts[2]

            source_data = json.loads(traj_path.read_text())
            exported_steps = extract_public_trajectory_steps(source_data)
            pass_num = pass_part.replace("pass_", "")
            destination = (
                target_root
                / mode
                / model_safe
                / instance_part.split("__")[0]
                / f"pass_{pass_num}_trajectory.json"
            )
            destination.parent.mkdir(parents=True, exist_ok=True)
            destination.write_text(json.dumps(exported_steps, indent=2))
            count += 1
    return count


def write_public_outputs(
    rows: list[dict[str, Any]],
    expected_passes: int,
    include_partial: bool,
    trajectory_results_dirs: list[Path],
    metrics_dir: Path,
) -> int:
    pass_csv = metrics_dir / "pass_level_metrics.csv"
    summary_json = metrics_dir / "summary_metrics.json"
    trajectories_dir = metrics_dir / "trajectories"
    write_pass_csv(rows, pass_csv)
    summary = build_summary(rows, include_partial=include_partial, expected_passes=expected_passes)
    summary_json.write_text(json.dumps(summary, indent=2))
    num_trajectories = export_trajectories(trajectory_results_dirs, trajectories_dir)
    print(f"📊 Pass-level CSV: {pass_csv}")
    print(f"🧾 Summary JSON: {summary_json}")
    print(f"🛰️  Exported trajectories: {num_trajectories} -> {trajectories_dir}")
    return num_trajectories


def main() -> None:
    load_dotenv()
    hf_home_default = "/tmp/huggingface_cache"
    if not os.environ.get("HF_HOME"):
        os.environ["HF_HOME"] = hf_home_default
    for var in ["HUGGINGFACE_HUB_CACHE", "TRANSFORMERS_CACHE", "SENTENCE_TRANSFORMERS_HOME"]:
        if not os.environ.get(var):
            os.environ[var] = os.environ["HF_HOME"]

    parser = argparse.ArgumentParser()
    parser.add_argument(
        "--task-type",
        "-t",
        choices=["sql", "swe", "both"],
        required=True,
        help="Task type to run.",
    )
    parser.add_argument(
        "--num-datapoints",
        "-n",
        type=int,
        default=None,
        help="Run only the first N datapoints for each selected task type.",
    )
    parser.add_argument(
        "--models",
        "-m",
        nargs="+",
        required=True,
        help="Model names to run.",
    )
    parser.add_argument(
        "--passes",
        "-k",
        type=int,
        default=3,
        help="Number of passes per (task, model, mode).",
    )
    parser.add_argument(
        "--modes",
        nargs="+",
        choices=["baseline", "ask_human", "full_info"],
        default=["baseline", "ask_human", "full_info"],
        help="Modes to run.",
    )
    parser.add_argument(
        "--num-concurrent-datapoints",
        "-c",
        type=int,
        default=10,
        help="Number of datapoints to set off concurrently.",
    )
    parser.add_argument(
        "--num-workers",
        "-w",
        type=int,
        default=9,
        help="Worker count passed to `hil sql`/`hil swe`.",
    )
    parser.add_argument(
        "--max-steps",
        type=int,
        default=200,
        help="Maximum agent steps per run.",
    )
    parser.add_argument(
        "--per-instance-cost-limit",
        type=float,
        default=100,
        help="Cost limit per pass in dollars.",
    )
    parser.add_argument(
        "--no-cleanup-docker",
        dest="cleanup_docker",
        action="store_false",
        help="Disable Docker cleanup.",
    )
    parser.set_defaults(cleanup_docker=True)
    parser.add_argument(
        "--agent-config-mapping",
        type=Path,
        required=True,
        help="YAML mapping task_type/mode/model to agent config YAML paths.",
    )
    parser.add_argument(
        "--judge-config",
        type=Path,
        required=True,
        help="YAML config for ask_human judge backend/model.",
    )
    parser.add_argument(
        "--output-dir",
        type=Path,
        default=Path("results"),
        help="Base output directory.",
    )
    parser.add_argument("--run-name", type=str, default=None, help="Optional run name.")
    parser.add_argument(
        "--workspace-dir",
        type=Path,
        default=Path("/tmp"),
        help="Parent directory where temporary run directories are created.",
    )
    parser.add_argument(
        "--keep-workspace",
        action="store_true",
        help="Keep temporary parent directory after run completion.",
    )
    parser.add_argument("--include-partial", action="store_true", help="Include datapoints that only partially completed all passes in the final metrics (default is to only include those that completed all passes)")
    parser.add_argument(
        "--rerun",
        action="store_true",
        help=(
            "If prior results exist for the same run name, model(s), and mode(s), only re-execute "
            "passes whose trajectory is missing or invalid (timeout / hiccup / env-died / unknown "
            "error). Valid existing passes are kept as-is and merged back into the original results "
            "directory. Has no effect if no prior results exist."
        ),
    )
    args = parser.parse_args()
    
    run_name = args.run_name or f"{args.task_type}_run_{datetime.now(timezone.utc).strftime('%Y%m%d_%H%M%S')}"
    output_dir = args.output_dir.resolve()
    workspace_parent = args.workspace_dir.resolve()
    workspace_parent.mkdir(parents=True, exist_ok=True)
    workspace_dir = Path(tempfile.mkdtemp(prefix=f"hil_bench_{run_name}_", dir=str(workspace_parent)))
    keep_workspace = bool(args.keep_workspace)

    print(f"📦 Loading HF dataset {HF_DATASET}")
    dataset = load_dataset(HF_DATASET, split="train")
    all_rows = [dict(row) for row in dataset]

    task_types = [args.task_type] if args.task_type in {"sql", "swe"} else ["sql", "swe"]
    combined_rows = []
    run_result_dirs = []

    print(f"🛠️ Temporary run directory: {workspace_dir}")
    owner_token = register_run_owner()
    try:
        for task_type in task_types:
            print(f"\n=== {task_type.upper()} setup ===")
            task_workspace = workspace_dir / task_type
            task_workspace.mkdir(parents=True, exist_ok=True)
            instances_path, task_folder, task_names, task_to_image = build_runtime_workspace(
                task_type=task_type,
                workspace_dir=task_workspace,
                rows=all_rows,
                num_datapoints=args.num_datapoints,
                models=args.models,
                num_concurrent_datapoints=args.num_concurrent_datapoints,
            )
            print(f"✅ Prepared {len(task_names)} {task_type.upper()} tasks")
            print(f"📄 Runtime instances file: {instances_path}")

            sub_run_name = run_name if len(task_types) == 1 else f"{run_name}_{task_type}"
            existing_run_dir = output_dir / sub_run_name

            if args.rerun and existing_run_dir.exists():
                needs_rerun = find_passes_needing_rerun(existing_run_dir, args.passes)
                if not needs_rerun:
                    print(f"✅ All passes for {task_type.upper()} are already valid — skipping rerun.")
                    run_results_dir = existing_run_dir
                else:
                    total_bad = sum(len(v) for v in needs_rerun.values())
                    print(
                        f"🔄 Rerun: {len(needs_rerun)} (model, mode) pair(s) have "
                        f"{total_bad} pass slot(s) needing rerun."
                    )
                    max_new_passes = max(len(v) for v in needs_rerun.values())

                    rerun_model_safes = {ms for (ms, _) in needs_rerun}
                    rerun_mode_names = {mn for (_, mn) in needs_rerun}
                    rerun_models = [
                        m for m in args.models
                        if m.replace("/", "_").replace(":", "_") in rerun_model_safes
                    ] or list(args.models)

                    if len(rerun_mode_names) == 1:
                        rerun_modes = [m for m in args.modes if m in rerun_mode_names]
                    else:
                        rerun_modes = list(args.modes)

                    rerun_args = copy.copy(args)
                    rerun_args.passes = max_new_passes
                    rerun_args.models = rerun_models
                    rerun_args.modes = rerun_modes
                    print(
                        f"   Models: {rerun_models}  Modes: {rerun_modes}  "
                        f"Passes (new): {max_new_passes}"
                    )
                    temp_run_name = (
                        f"{sub_run_name}__rerun_{datetime.now(timezone.utc).strftime('%Y%m%d_%H%M%S')}"
                    )
                    exit_code, temp_run_dir = run_hil_cli(
                        task_type=task_type,
                        args=rerun_args,
                        instances_path=instances_path,
                        run_name=temp_run_name,
                    )
                    if exit_code != 0:
                        raise RuntimeError(
                            f"`hil {task_type}` rerun exited with code {exit_code}"
                        )
                    if not temp_run_dir.exists():
                        raise FileNotFoundError(
                            f"Could not resolve rerun output directory for {temp_run_name}"
                        )
                    print(f"\n🔀 Merging rerun results into {existing_run_dir}")
                    merge_rerun_results(
                        original_run_dir=existing_run_dir,
                        temp_run_dir=temp_run_dir,
                        needs_rerun=needs_rerun,
                    )
                    shutil.rmtree(temp_run_dir, ignore_errors=True)
                    run_results_dir = existing_run_dir
            else:
                exit_code, run_results_dir = run_hil_cli(
                    task_type=task_type,
                    args=args,
                    instances_path=instances_path,
                    run_name=sub_run_name,
                )
                if exit_code != 0:
                    raise RuntimeError(f"`hil {task_type}` exited with code {exit_code}")
                if not run_results_dir.exists():
                    raise FileNotFoundError(
                        f"Could not resolve run output directory for {sub_run_name}"
                    )

            if task_type == "swe" and args.cleanup_docker:
                removed_containers = 0
                for task_name in task_names:
                    image_name = task_to_image.get(task_name)
                    if image_name:
                        removed_containers += cleanup_swe_containers_for_image(image_name)
                if removed_containers > 0:
                    print(f"🧹 Removed {removed_containers} SWE container(s) after run cleanup")

            rows = parse_metrics_rows(
                task_type=task_type,
                results_dir=run_results_dir,
                expected_passes=args.passes,
                log_dir=str(workspace_dir) if keep_workspace else None,
            )
            combined_rows.extend(rows)
            run_result_dirs.append(run_results_dir)

            metrics_dir = run_results_dir / "public_metrics"
            print(f"\n📊 Writing {task_type.upper()} metrics...")
            write_public_outputs(
                rows=rows,
                expected_passes=args.passes,
                include_partial=args.include_partial,
                trajectory_results_dirs=[run_results_dir],
                metrics_dir=metrics_dir,
            )

        if len(task_types) > 1:
            print("\n📊 Writing combined SQL+SWE metrics...")
            combined_metrics_dir = output_dir / run_name / "public_metrics"
            write_public_outputs(
                rows=combined_rows,
                expected_passes=args.passes,
                include_partial=args.include_partial,
                trajectory_results_dirs=run_result_dirs,
                metrics_dir=combined_metrics_dir,
            )
        print("\n✅ Done")
    finally:
        unregister_run_owner(owner_token)
        if workspace_dir.exists() and not keep_workspace:
            shutil.rmtree(workspace_dir, ignore_errors=True)
            print(f"🧹 Cleaned workspace: {workspace_dir}")
        elif workspace_dir.exists():
            print(f"📁 Kept workspace: {workspace_dir}")


if __name__ == "__main__":
    main()
