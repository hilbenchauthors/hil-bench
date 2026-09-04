import io
import json
import sqlite3
import time
from collections import Counter
from pathlib import Path
from typing import Any

import pandas as pd

DATABASE_PATH = Path("/data/database.sqlite")
SUBMISSION_PATH = Path("/harbor_shared/submitted_query.sql")
GROUND_TRUTH_PATH = Path("/tests/ground_truth.sql")
GOLDEN_OUTPUT_PATH = Path("/tests/golden_output.csv")
REWARD_DIR = Path("/logs/verifier")
REWARD_PATH = REWARD_DIR / "reward.json"
REWARD_TXT_PATH = REWARD_DIR / "reward.txt"
ASK_HUMAN_METRICS_PATH = Path("/harbor_shared/ask_human_metrics.json")
MAX_QUERY_EXECUTION_TIMEOUT = 300


def execute_sql(db_path: str, query: str) -> tuple[str | None, pd.DataFrame | None]:
    if not query or not query.strip():
        return "Error: empty query", None
    try:
        with sqlite3.connect(f"file:{db_path}?mode=ro", uri=True) as conn:
            start = time.time()

            def progress_handler():
                if time.time() - start > MAX_QUERY_EXECUTION_TIMEOUT:
                    return 1

            conn.set_progress_handler(progress_handler, 1000)
            cursor = conn.cursor()
            try:
                cursor.execute(query)
                if cursor.description is not None:
                    columns = [description[0] for description in cursor.description]
                    data = cursor.fetchall()
                    return None, pd.DataFrame(data, columns=columns)
                conn.commit()
                return "Error: non-SELECT query", None
            except Exception as e:
                return f"Error: {e}", None
            finally:
                conn.set_progress_handler(None, 0)
    except sqlite3.OperationalError as e:
        if "interrupted" in str(e).lower():
            return f"Error: query timed out after {MAX_QUERY_EXECUTION_TIMEOUT} seconds", None
        if "attempt to write a readonly database" in str(e).lower():
            return "Error: non-SELECT query", None
        return f"Error: {e}", None
    except Exception as e:
        return f"Error: {e}", None


def tolerant_counter(inp: pd.Series | list[frozenset], tol: float = 1e-2) -> dict[Any, int]:
    counter = {}
    if isinstance(inp, pd.Series):
        for value in inp:
            if pd.isna(value):
                value = None
            if pd.isna(value) or not isinstance(value, (int, float)):
                key = value
            else:
                key = value if tol == 0 else round(value / tol) * tol
            counter[key] = counter.get(key, 0) + 1
    else:
        counter = dict(Counter(inp))
    return counter


def compare_pandas_outputs_helper(gt_df: pd.DataFrame, pred_df: pd.DataFrame) -> bool:
    if len(gt_df) != len(pred_df):
        return False
    if pred_df.shape[1] < gt_df.shape[1]:
        return False
    if gt_df.shape == pred_df.shape:
        gt_df_row_counter = gt_df.apply(
            lambda row: frozenset(tolerant_counter(row).items()), axis=1
        ).tolist()
        pred_df_row_counter = pred_df.apply(
            lambda row: frozenset(tolerant_counter(row).items()), axis=1
        ).tolist()
        gt_df_counter = tolerant_counter(gt_df_row_counter)
        pred_df_counter = tolerant_counter(pred_df_row_counter)
        return gt_df_counter == pred_df_counter
    pred_df_row_counters = pred_df.apply(tolerant_counter, axis=1).tolist()
    used_pred_df_indices = [False] * len(pred_df_row_counters)
    for _, gt_row in gt_df.iterrows():
        gt_counter = tolerant_counter(gt_row)
        match_found_for_gt_row = False
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


def _normalize_single_dataframe(df: pd.DataFrame) -> pd.DataFrame:
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
    expected_sorted: bool = False,
    required_unique: bool = False,
    no_extra_columns_allowed: bool = False,
) -> bool:
    gt_df = _normalize_single_dataframe(gt_df)
    pred_df = _normalize_single_dataframe(pred_df)
    if no_extra_columns_allowed and gt_df.shape[1] != pred_df.shape[1]:
        return False
    original_gt_df = gt_df.copy()
    collapsed_gt_df = gt_df.drop_duplicates().reset_index(drop=True)
    original_pred_df = pred_df.copy()
    collapsed_pred_df = pred_df.drop_duplicates().reset_index(drop=True)
    for df1 in [original_gt_df, collapsed_gt_df]:
        for df2 in [original_pred_df] if required_unique else [original_pred_df, collapsed_pred_df]:
            if compare_pandas_outputs_helper(df1, df2):
                return True
    return False


def parse_golden_output(golden_output_str: str) -> pd.DataFrame:
    golden_output_str = golden_output_str.strip()
    df = pd.read_csv(io.StringIO(golden_output_str), dtype=str)
    for col in df.columns:
        col_values = df[col].dropna()
        if len(col_values) == 0:
            continue
        has_leading_zeros = col_values.str.match(r"^0\d").any()
        if has_leading_zeros:
            continue
        numeric_col = pd.to_numeric(df[col], errors="coerce")
        if numeric_col.notna().sum() == df[col].notna().sum():
            df[col] = numeric_col
    return df


def get_ask_human_metrics() -> dict:
    if ASK_HUMAN_METRICS_PATH.exists():
        try:
            data = json.loads(ASK_HUMAN_METRICS_PATH.read_text())
            return {
                "n_questions": int(data.get("total_questions", len(data.get("questions", [])))),
                "n_blockers": int(data.get("n_blockers", 0)),
                "blockers_resolved": int(data.get("blockers_resolved", 0)),
                "precision": float(data.get("precision", 0.0)),
                "recall": float(data.get("recall", 0.0)),
                "f1": float(data.get("f1", 0.0)),
            }
        except Exception:
            pass
    return {
        "n_questions": 0,
        "n_blockers": 0,
        "blockers_resolved": 0,
        "precision": 0.0,
        "recall": 0.0,
        "f1": 0.0,
    }


def main():
    REWARD_DIR.mkdir(parents=True, exist_ok=True)

    solve = 0
    sub_err = None
    gt_err = None

    if not SUBMISSION_PATH.exists():
        print("No submission found — score is 0")
    else:
        submitted_query = SUBMISSION_PATH.read_text().strip()
        ground_truth_query = GROUND_TRUTH_PATH.read_text().strip()
        sub_err, sub_df = execute_sql(str(DATABASE_PATH), submitted_query)
        gt_err, gt_df = execute_sql(str(DATABASE_PATH), ground_truth_query)

        if sub_df is None or gt_df is None:
            solve = 0
        else:
            solve = int(compare_pandas_outputs(gt_df, sub_df))

        if gt_df is not None and GOLDEN_OUTPUT_PATH.exists():
            golden_df = parse_golden_output(GOLDEN_OUTPUT_PATH.read_text())
            if not compare_pandas_outputs(golden_df, gt_df):
                print("Warning: ground truth SQL output mismatches golden_output.csv")
        if sub_err:
            print(f"Submission error: {sub_err}")
        if gt_err:
            print(f"Ground truth error: {gt_err}")

    ask_metrics = get_ask_human_metrics()

    reward = {
        "solve": solve,
        "precision": ask_metrics["precision"],
        "recall": ask_metrics["recall"],
        "f1": ask_metrics["f1"],
    }

    REWARD_PATH.write_text(json.dumps(reward, indent=2))
    REWARD_TXT_PATH.write_text(str(solve))
    print(json.dumps(reward, indent=2))


if __name__ == "__main__":
    main()
