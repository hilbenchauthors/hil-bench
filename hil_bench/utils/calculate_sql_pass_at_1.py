from __future__ import annotations

import io
import json
import sqlite3
import time
from collections import Counter
from concurrent.futures import ThreadPoolExecutor, as_completed
from pathlib import Path
from typing import Any

import pandas as pd

# =============================================================================
# Constants
# =============================================================================

MAX_QUERY_EXECUTION_TIMEOUT = 300  # 5 minutes


# =============================================================================
# SQL Execution
# =============================================================================


def execute_sql(db_path: str, query: str) -> tuple[str | None, pd.DataFrame | None]:
    """
    Execute a SQL query against a SQLite database.

    Args:
        db_path: Path to the SQLite database file
        query: SQL query to execute

    Returns:
        Tuple of (error_message, result_dataframe)
        - If successful: (None, DataFrame)
        - If error: (error_string, None)
    """
    if not query or not query.strip():
        return "Error: empty query", None

    try:
        with sqlite3.connect(f"file:{db_path}?mode=ro", uri=True) as conn:
            start = time.time()

            def progress_handler():
                if time.time() - start > MAX_QUERY_EXECUTION_TIMEOUT:
                    return 1  # returning non-zero value cancels the query

            conn.set_progress_handler(progress_handler, 1000)  # check every 1000 operations
            cursor = conn.cursor()
            try:
                cursor.execute(query)
                if cursor.description is not None:  # SELECT, WITH, or other row-returning query
                    columns = [description[0] for description in cursor.description]
                    data = cursor.fetchall()
                    df = pd.DataFrame(data, columns=columns)
                    return None, df
                else:  # INSERT, UPDATE, DELETE, CREATE, etc.
                    conn.commit()
                    return "Error: non-SELECT query", None
            except Exception as e:
                return f"Error: {e}", None
            finally:
                conn.set_progress_handler(None, 0)  # disable progress handler always
    except sqlite3.OperationalError as e:
        if "interrupted" in str(e).lower():
            return f"Error: query timed out after {MAX_QUERY_EXECUTION_TIMEOUT} seconds", None
        if "attempt to write a readonly database" in str(e).lower():
            return "Error: non-SELECT query", None
        return f"Error: {e}", None
    except Exception as e:
        return f"Error: {e}", None


# =============================================================================
# DataFrame Comparison
# =============================================================================


def tolerant_counter(inp: pd.Series | list[frozenset], tol: float = 1e-2) -> dict[Any, int]:
    counter = {}
    if isinstance(inp, pd.Series):
        for value in inp:
            # Convert any NaN-y values to None because NaN is weird with frozensets
            if pd.isna(value):
                value = None
            # Non-numeric types must match exactly
            if pd.isna(value) or not isinstance(value, (int, float)):
                key = value
            else:  # Numbers must be within a tolerance
                if tol == 0:
                    key = value
                else:
                    key = round(value / tol) * tol
            counter[key] = counter.get(key, 0) + 1
    else:
        counter = dict(Counter(inp))
    return counter


def compare_pandas_outputs_helper(gt_df: pd.DataFrame, pred_df: pd.DataFrame) -> bool:
    # Check for same number of rows (extra columns ok)
    if len(gt_df) != len(pred_df):
        return False
    # If pred DF is missing some columns, fail
    if pred_df.shape[1] < gt_df.shape[1]:
        return False
    # Check the contents
    if gt_df.shape == pred_df.shape:  # faster method if num rows and num cols are equal
        # First get number of times each value appears per row
        gt_df_row_counter = gt_df.apply(
            lambda row: frozenset(tolerant_counter(row).items()), axis=1
        ).tolist()
        pred_df_row_counter = pred_df.apply(
            lambda row: frozenset(tolerant_counter(row).items()), axis=1
        ).tolist()
        # Next get how often each unique row (counted set of values) appears
        gt_df_counter = tolerant_counter(gt_df_row_counter)
        pred_df_counter = tolerant_counter(pred_df_row_counter)
        return gt_df_counter == pred_df_counter
    # For every row in ground truth, can we find a matching row in the prediction
    pred_df_row_counters = pred_df.apply(tolerant_counter, axis=1).tolist()
    used_pred_df_indices = [False] * len(pred_df_row_counters)
    for _, gt_row in gt_df.iterrows():
        gt_counter = tolerant_counter(gt_row)
        match_found_for_gt_row = False
        # Find an unused row in pred DF that is a superset of the current GT DF row
        for i, pred_counter in enumerate(pred_df_row_counters):
            if not used_pred_df_indices[i] and all(
                gt_counter[key] <= pred_counter.get(key, 0) for key in gt_counter
            ):
                used_pred_df_indices[i] = True
                match_found_for_gt_row = True
                break
        if not match_found_for_gt_row:
            return False
    return True


def _count_matched_rows(gt_df: pd.DataFrame, pred_df: pd.DataFrame) -> int:
    """
    Count how many rows in gt_df find a tolerant match in pred_df (multiset intersection).

    Uses the same tolerant per-value matching as compare_pandas_outputs_helper but
    does not early-bail on row count mismatch, returning a count instead of bool.
    This is used to compute Jaccard IoU: matched / (|gt| + |pred| - matched).
    """
    if pred_df.shape[1] < gt_df.shape[1]:
        return 0
    pred_row_counters = pred_df.apply(tolerant_counter, axis=1).tolist()
    used = [False] * len(pred_row_counters)
    matched = 0
    for _, gt_row in gt_df.iterrows():
        gt_counter = tolerant_counter(gt_row)
        for i, pred_counter in enumerate(pred_row_counters):
            if not used[i] and all(gt_counter[k] <= pred_counter.get(k, 0) for k in gt_counter):
                used[i] = True
                matched += 1
                break
    return matched


def _normalize_single_dataframe(df: pd.DataFrame) -> pd.DataFrame:
    """
    For each column:
    - If has leading zeros (e.g., "01234") → keep as string
    - If all values are numeric → convert to float
    - Otherwise → keep as string
    """
    df = df.copy()
    for col in df.columns:
        col_str = df[col].astype(str)
        has_leading_zeros = col_str.str.match(r"^0\d").any()
        if has_leading_zeros:
            df[col] = col_str
        else:
            numeric = pd.to_numeric(df[col], errors="coerce")
            if numeric.notna().sum() == df[col].notna().sum():
                df[col] = numeric
            else:
                df[col] = col_str
    return df


def compare_pandas_outputs(
    gt_df: pd.DataFrame,
    pred_df: pd.DataFrame,
    expected_sorted: bool = False,  # TODO: handle
    required_unique: bool = False,  # TODO: handle
    no_extra_columns_allowed: bool = False,  # TODO: too contrived flag
    return_jaccard: bool = False,
):
    """
    Compare two DataFrames for output equivalence.

    When return_jaccard=False (default): returns True/False (original behavior).
    When return_jaccard=True: returns a float Jaccard IoU in [0.0, 1.0] measuring
    row-level overlap between the original (non-collapsed) normalized DataFrames.
      Jaccard = matched_rows / (|gt_rows| + |pred_rows| - matched_rows)
    Edge cases: both empty → 1.0; one empty → 0.0.
    """
    # Normalize types between the two DataFrames before comparison
    gt_df = _normalize_single_dataframe(gt_df)
    pred_df = _normalize_single_dataframe(pred_df)

    if return_jaccard:
        if no_extra_columns_allowed and gt_df.shape[1] != pred_df.shape[1]:
            return 0.0
        n_gt, n_pred = len(gt_df), len(pred_df)
        if n_gt == 0 and n_pred == 0:
            return 1.0
        if n_gt == 0 or n_pred == 0:
            return 0.0
        matched = _count_matched_rows(gt_df, pred_df)
        union = n_gt + n_pred - matched
        return matched / union if union > 0 else 0.0

    # We do not consider distinctiveness by default; as long as two of {original, collapsed} x {gt, pred} match, we say they are equal
    # However, if required unique, then we don't count collapsed preds, because the original preds should already be unique
    if no_extra_columns_allowed:
        if gt_df.shape[1] != pred_df.shape[1]:
            return False  # number of columns must match exactly
    original_gt_df = gt_df.copy()
    collapsed_gt_df = gt_df.drop_duplicates().reset_index(drop=True)
    original_pred_df = pred_df.copy()
    collapsed_pred_df = pred_df.drop_duplicates().reset_index(drop=True)
    for df1 in [original_gt_df, collapsed_gt_df]:
        for df2 in [original_pred_df] if required_unique else [original_pred_df, collapsed_pred_df]:
            if compare_pandas_outputs_helper(df1, df2):
                return True
    return False


# =============================================================================
# Golden Output Parsing
# =============================================================================


def parse_golden_output(golden_output_str: str) -> pd.DataFrame:
    golden_output_str = golden_output_str.strip()
    try:
        # First read all columns as strings initially to preserve any leading zeros
        df = pd.read_csv(io.StringIO(golden_output_str), dtype=str)
        # Then convert columns that are purely numeric (no leading zeros) to proper numeric types
        for col in df.columns:
            col_values = df[col].dropna()
            if len(col_values) == 0:
                continue
            has_leading_zeros = col_values.str.match(r"^0\d").any()
            if has_leading_zeros:
                continue
            numeric_col = pd.to_numeric(df[col], errors="coerce")
            # Only convert if ALL non-null values successfully converted
            if numeric_col.notna().sum() == df[col].notna().sum():
                df[col] = numeric_col
        return df
    except Exception as e:
        raise ValueError(f"Could not parse golden_output as CSV: {e}")


# =============================================================================
# Instance Evaluation
# =============================================================================


def evaluate_single_sql_instance(
    instance_id: str,
    pred_data: dict[str, Any],
    instance_info: dict[str, Any],
    tasks_dir: Path,
) -> tuple[str, dict[str, Any], bool]:
    """
    Evaluate a single SQL instance.

    Args:
        instance_id: The instance identifier
        pred_data: Prediction data including 'model_patch' (the SQL query)
        instance_info: Instance info including problem_statement and env
        tasks_dir: Base directory for resolving relative paths

    Returns:
        Tuple of (instance_id, result_dict, is_correct)
    """
    result: dict[str, Any] = {
        "instance_id": instance_id,
        "completed": False,
        "resolved": False,
        "status": "error",  # Will be updated to "correct"/"incorrect"
    }

    try:
        problem_statement = instance_info.get("problem_statement", {})
        env = instance_info.get("env", {})

        # Get ground truth query
        gt_sql = problem_statement.get("ground_truth_query", "")
        if not gt_sql:
            result["error"] = "No ground_truth_query in instance"
            return (instance_id, result, False)

        # Get predicted query
        pred_sql = pred_data.get("model_patch", "")
        if not pred_sql or not pred_sql.strip():
            result["error"] = "No model_patch (predicted SQL) in prediction"
            result["status"] = "Error: empty query"
            result["completed"] = True
            return (instance_id, result, False)

        # Get database path
        db_path = env.get("base_db_path", "")
        if not db_path:
            result["error"] = "No base_db_path in instance env"
            return (instance_id, result, False)

        # Resolve relative path
        # db_path may be relative to git root (e.g., "research_evals/hil_bench/sql_tasks/...")
        # Walk up from tasks_dir to find the correct base directory
        if not Path(db_path).is_absolute():
            resolved_db_path = None
            # Resolve tasks_dir to absolute path first to avoid Path.parent getting stuck at "."
            current = tasks_dir.resolve()
            for _ in range(10):  # Walk up to 10 levels
                candidate = current / db_path
                if candidate.exists():
                    resolved_db_path = str(candidate)
                    break
                if current == current.parent:
                    break  # Reached filesystem root
                current = current.parent
            if resolved_db_path is None:
                result["error"] = (
                    f"Database not found: {db_path} (searched from {tasks_dir.resolve()} upward)"
                )
                return (instance_id, result, False)
            db_path = resolved_db_path

        if not Path(db_path).exists():
            result["error"] = f"Database not found: {db_path}"
            return (instance_id, result, False)

        # Get comparison options
        expected_sorted = problem_statement.get("expected_sorted", False)
        required_unique = problem_statement.get("required_unique", False)
        no_extra_columns_allowed = problem_statement.get("no_extra_columns_allowed", False)

        # Execute ground truth query
        gt_error, gt_df = execute_sql(db_path, gt_sql)
        if gt_df is None:
            result["error"] = f"Ground truth query failed: {gt_error}"
            return (instance_id, result, False)

        # Execute predicted query
        pred_error, pred_df = execute_sql(db_path, pred_sql)
        result["completed"] = True

        if pred_df is None:
            result["error"] = pred_error
            result["status"] = pred_error or "Error: query failed"
            return (instance_id, result, False)

        # Compare results
        is_correct = compare_pandas_outputs(
            gt_df,
            pred_df,
            expected_sorted=expected_sorted,
            required_unique=required_unique,
            no_extra_columns_allowed=no_extra_columns_allowed,
        )

        result["resolved"] = is_correct
        result["status"] = "correct" if is_correct else "incorrect"
        result["gt_rows"] = len(gt_df)
        result["pred_rows"] = len(pred_df)
        result["gt_cols"] = len(gt_df.columns)
        result["pred_cols"] = len(pred_df.columns)

        # Include actual query results (truncated for large results)
        max_rows_to_store = 100
        result["gt_query"] = gt_sql
        result["pred_query"] = pred_sql
        result["gt_result"] = {
            "columns": list(gt_df.columns),
            "rows": gt_df.head(max_rows_to_store).values.tolist(),
            "row_count": len(gt_df),
            "truncated": len(gt_df) > max_rows_to_store,
        }
        result["pred_result"] = {
            "columns": list(pred_df.columns),
            "rows": pred_df.head(max_rows_to_store).values.tolist(),
            "row_count": len(pred_df),
            "truncated": len(pred_df) > max_rows_to_store,
        }
        result["gt_result_csv"] = gt_df.head(max_rows_to_store).to_csv(index=False)
        result["pred_result_csv"] = pred_df.head(max_rows_to_store).to_csv(index=False)
        return (instance_id, result, is_correct)
    except Exception as e:
        result["error"] = str(e)
        result["status"] = f"Error: {e}"
        return (instance_id, result, False)


# =============================================================================
# Cost/Runtime Extraction
# =============================================================================


def get_cost_runtime(trajectory_dir: str | Path) -> dict[str, dict[str, Any]]:
    """
    Load per-instance cost, runtime, and step count from trajectory files.

    Returns:
        dict: Mapping of instance_id to dict with 'cost', 'runtime', 'num_steps' keys
    """
    trajectory_path = Path(trajectory_dir)
    instance_metrics: dict[str, dict[str, Any]] = {}

    # Find all .traj files in subdirectories
    traj_files = list(trajectory_path.glob("**/*.traj"))

    for traj_file in traj_files:
        try:
            traj_data = json.loads(traj_file.read_text())
            instance_id = traj_file.stem
            cost = 0.0
            if "info" in traj_data and "model_stats" in traj_data["info"]:
                cost = traj_data["info"]["model_stats"].get("instance_cost", 0.0)

            # Calculate total runtime by summing execution_time from all steps
            runtime = 0.0
            num_steps = 0
            if "trajectory" in traj_data:
                trajectory = traj_data["trajectory"]
                num_steps = len(trajectory)
                for step in trajectory:
                    if "execution_time" in step:
                        runtime += step["execution_time"]

            instance_metrics[instance_id] = {
                "cost": cost,
                "runtime": runtime,
                "num_steps": num_steps,
            }
        except Exception:
            pass

    return instance_metrics


# =============================================================================
# Main Entry Point
# =============================================================================


def calculate_sql_pass_at_1(
    trajectory_dir: str | Path,
    tasks_dir: str | Path,
    max_workers: int = 4,
    instances_file: str | Path | None = None,
) -> dict[str, Any]:
    """
    Calculate pass@1 for SQL task-type tasks.

    Pass@1 = percentage of problems where the generated SQL query produces
    the correct result when executed against the database.

    Args:
        trajectory_dir: Path to directory containing preds.json
        tasks_dir: Path to tasks directory containing instances.json
        max_workers: Number of parallel workers for evaluation
        instances_file: Explicit path to the instances JSON file that was used
            for the evaluation. When provided, this takes priority over
            auto-discovery in tasks_dir.  This is critical when the tasks
            directory contains multiple instances files (e.g. instances.json
            and instances_val.json) to ensure the ground-truth SQL matches
            the questions the agent was given.

    Returns:
        dict with pass@1 results:
        {
            "total_instances": int,
            "pass_at_1_count": int,
            "pass_at_1_rate": float (0-100),
            "resolved_instances": list[str],
            "patches_generated": int,
            "patch_generation_rate": float (0-100),
            "total_cost": float,
            "total_runtime": float,
            "instances": dict,
            "results": dict,
        }
    """
    trajectory_path = Path(trajectory_dir)
    tasks_path = Path(tasks_dir)

    print(f"🧮 Calculating SQL pass@1 for: {trajectory_dir}")

    # Load predictions
    preds_file = trajectory_path / "preds.json"
    if not preds_file.exists():
        raise ValueError(f"❌ Predictions file not found: {preds_file}")

    predictions: dict[str, dict[str, Any]] = json.loads(preds_file.read_text())
    if not predictions:
        raise ValueError("❌ No predictions found")

    total_instances = len(predictions)
    print(f"📊 Found {total_instances} predictions")

    # Load instances to get ground truth info.
    # When an explicit instances_file is given, use it directly — this
    # prevents picking up a stale instances.json that lives alongside
    # the correct instances_val.json in the same directory.
    resolved_instances_file: Path
    if instances_file is not None:
        resolved_instances_file = Path(instances_file)
        if not resolved_instances_file.exists():
            raise ValueError(f"❌ Provided instances file not found: {resolved_instances_file}")
    else:
        resolved_instances_file = tasks_path / "instances.json"
        if not resolved_instances_file.exists():
            dirname = tasks_path.name
            alt_file = tasks_path / f"{dirname}.json"
            if alt_file.exists():
                resolved_instances_file = alt_file
            else:
                json_files = [
                    f for f in tasks_path.glob("*.json") if not f.name.endswith("_registry.json")
                ]
                if json_files:
                    resolved_instances_file = json_files[0]
                else:
                    raise ValueError(
                        f"❌ Instances file not found: {tasks_path / 'instances.json'} (also tried {alt_file})"
                    )

    print(f"📄 Using instances file: {resolved_instances_file}")
    instances_list = json.loads(resolved_instances_file.read_text())

    # Build instance lookup by ID
    # The instance ID in predictions may have suffixes like "__model__mode__pass_1"
    # We need to extract the original instance ID
    instances_by_id: dict[str, dict[str, Any]] = {}
    for inst in instances_list:
        inst_id = inst.get("problem_statement", {}).get("id", "")
        if inst_id:
            instances_by_id[inst_id] = inst

    print(f"📊 Found {len(instances_by_id)} instance definitions")

    # Get cost/runtime metrics
    instance_metrics = get_cost_runtime(trajectory_dir)
    total_cost = sum(m.get("cost", 0) for m in instance_metrics.values())
    total_runtime = sum(m.get("runtime", 0) for m in instance_metrics.values())

    # Evaluate instances
    results: dict[str, dict[str, Any]] = {}
    resolved_ids: list[str] = []

    def extract_original_id(full_id: str) -> str:
        """Extract original instance ID from potentially suffixed ID."""
        # Pattern: {original_id}__{model}__{mode}__pass_{n}
        # or just {original_id}
        parts = full_id.split("__")
        return parts[0]

    print(f"\n🔬 Running SQL evaluation with {max_workers} workers...")

    if max_workers <= 1:
        # Sequential execution
        for instance_id, pred_data in predictions.items():
            original_id = extract_original_id(instance_id)
            instance_info = instances_by_id.get(original_id, {})

            if not instance_info:
                print(f"   ⚠️  [{instance_id}] No instance info found for {original_id}")
                continue

            inst_id, result, is_correct = evaluate_single_sql_instance(
                instance_id, pred_data, instance_info, tasks_path
            )
            results[inst_id] = result
            if is_correct:
                resolved_ids.append(inst_id)
                print(f"   ✅ [{inst_id}] CORRECT")
            else:
                error = result.get("error", "incorrect result")
                print(f"   ❌ [{inst_id}] {error}")
    else:
        # Parallel execution
        with ThreadPoolExecutor(max_workers=max_workers) as executor:
            future_to_instance = {}
            for instance_id, pred_data in predictions.items():
                original_id = extract_original_id(instance_id)
                instance_info = instances_by_id.get(original_id, {})

                if not instance_info:
                    print(f"   ⚠️  [{instance_id}] No instance info found for {original_id}")
                    continue

                future = executor.submit(
                    evaluate_single_sql_instance,
                    instance_id,
                    pred_data,
                    instance_info,
                    tasks_path,
                )
                future_to_instance[future] = instance_id

            for future in as_completed(future_to_instance):
                try:
                    inst_id, result, is_correct = future.result()
                    results[inst_id] = result
                    if is_correct:
                        resolved_ids.append(inst_id)
                        print(f"   ✅ [{inst_id}] CORRECT")
                    else:
                        error = result.get("error", "incorrect result")
                        print(f"   ❌ [{inst_id}] {error}")
                except Exception as e:
                    instance_id = future_to_instance[future]
                    print(f"   ❌ [{instance_id}] Exception: {e}")
                    results[instance_id] = {
                        "instance_id": instance_id,
                        "completed": False,
                        "resolved": False,
                        "error": str(e),
                    }

    print(f"\n✅ SQL evaluation complete: {len(resolved_ids)}/{total_instances} correct")

    patches_generated = sum(
        1 for pred_data in predictions.values() if pred_data.get("model_patch", "").strip()
    )

    # Merge trajectory metrics (num_steps, cost, runtime) into results
    for inst_id, result in results.items():
        if inst_id in instance_metrics:
            metrics = instance_metrics[inst_id]
            result["num_steps"] = metrics.get("num_steps", 0)
            result["cost"] = metrics.get("cost", 0.0)
            result["runtime"] = metrics.get("runtime", 0.0)

    return {
        "total_instances": total_instances,
        "pass_at_1_count": len(resolved_ids),
        "pass_at_1_rate": (len(resolved_ids) / total_instances) * 100 if total_instances > 0 else 0,
        "resolved_instances": resolved_ids,
        "patches_generated": patches_generated,
        "patch_generation_rate": (
            (patches_generated / total_instances) * 100 if total_instances > 0 else 0
        ),
        "total_cost": total_cost,
        "total_runtime": total_runtime,
        "instances": instance_metrics,
        "results": results,
    }


def print_sql_pass_at_1_summary(results: dict | None) -> None:
    """Print a formatted summary of SQL pass@1 results."""
    if results is None:
        return

    print("\n" + "=" * 60)
    print("🎯 SQL PASS@1 EVALUATION")
    print("=" * 60)

    print(
        f"📊 PASS@1: {results['pass_at_1_rate']:.1f}% "
        f"({results['pass_at_1_count']}/{results['total_instances']})"
    )
    print(f"📝 Queries generated: {results['patches_generated']}")
    print(f"✅ Correct queries: {results['pass_at_1_count']}")

    if results.get("total_cost", 0) > 0:
        print(f"💰 Total cost: ${results['total_cost']:.4f}")
        if results["pass_at_1_count"] > 0:
            cost_per_success = results["total_cost"] / results["pass_at_1_count"]
            print(f"💰 Cost per success: ${cost_per_success:.4f}")

    if results.get("total_runtime", 0) > 0:
        print(f"⏱️  Total runtime: {results['total_runtime']:.1f}s")

    print("=" * 60 + "\n")
