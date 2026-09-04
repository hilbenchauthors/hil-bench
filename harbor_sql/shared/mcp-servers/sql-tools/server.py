"""
SQL database tools MCP server:
- get_database_info
- get_table_info
- get_column_info
- execute_sql
- submit_sql
"""

import os
import sqlite3
import subprocess
import sys
from pathlib import Path

import pandas as pd

DATA_DIR = Path(os.environ.get("DATA_DIR", "/data"))
DATABASE_PATH = DATA_DIR / "database.sqlite"
DESCRIPTIONS_DIR = DATA_DIR / "database_description"
SUBMISSION_FILE = Path(os.environ.get("SUBMISSION_FILE", "/harbor_shared/submitted_query.sql"))
DEFAULT_SQL_QUERY_TIMEOUT_SECONDS = 1200.0
QUERY_WORKER_ARG = "--execute-query-worker"


def _query_timeout_seconds() -> float:
    raw = os.environ.get("SQL_QUERY_TIMEOUT_SECONDS", str(DEFAULT_SQL_QUERY_TIMEOUT_SECONDS))
    try:
        timeout = float(raw)
    except ValueError:
        return DEFAULT_SQL_QUERY_TIMEOUT_SECONDS
    return timeout if timeout > 0 else DEFAULT_SQL_QUERY_TIMEOUT_SECONDS


def _execute_sql_direct(database_path: Path, query: str, max_rows: int = 200) -> str:
    try:
        with sqlite3.connect(f"file:{database_path}?mode=ro", uri=True) as conn:
            cursor = conn.cursor()
            try:
                cursor.execute(query)
                if cursor.description is not None:
                    columns = [description[0] for description in cursor.description]
                    data = cursor.fetchall()
                    df = pd.DataFrame(data, columns=columns)
                    if df.empty:
                        return "Query executed successfully. No results returned."
                    if len(df) > max_rows:
                        df = df.head(max_rows)
                        return (
                            f"Query executed successfully. Result truncated to the first {max_rows} rows:\n"
                            f"{df.to_csv(index=False)}"
                        )
                    return f"Query executed successfully:\n{df.to_csv(index=False)}"
                return "Error: non-SELECT query"
            except sqlite3.OperationalError as e:
                if "attempt to write a readonly database" in str(e).lower():
                    return "Error: non-SELECT query"
                return f"Error: {e}"
            except Exception as e:
                return f"Error: {e}"
    except Exception as e:
        return f"Error executing query: {e}"


if __name__ == "__main__" and len(sys.argv) == 3 and sys.argv[1] == QUERY_WORKER_ARG:
    print(_execute_sql_direct(Path(sys.argv[2]), sys.stdin.read()), end="")
    raise SystemExit(0)


from fastmcp import FastMCP

mcp = FastMCP("sql-tools")


@mcp.tool()
def get_database_info(database_name: str) -> dict | str:
    """Retrieves information about a given database in dictionary form. Dictionary keys are table names, dictionary values are their descriptions. If the database doesn't exist, returns an error message."""
    table_descriptions_path = DESCRIPTIONS_DIR / "table_descriptions.csv"
    try:
        df = pd.read_csv(table_descriptions_path)
        info = dict(zip(df["table_name"], df["table_description"]))
        return info
    except FileNotFoundError:
        return f"Error: database {database_name} doesn't exist"


@mcp.tool()
def get_table_info(database_name: str, table_name: str) -> dict | str:
    """Retrieves information about a given table in dictionary form. Includes its description and a list of its columns. If the table doesn't exist, returns an error message."""
    table_lowered = table_name.lower()
    error_msg = f"Error: table {table_name} in database {database_name} doesn't exist"
    info = {}

    table_descriptions_path = DESCRIPTIONS_DIR / "table_descriptions.csv"
    try:
        df = pd.read_csv(table_descriptions_path)
        df_slice = df[df["table_name"] == table_name]
        if len(df_slice) == 0:
            df_slice = df[df["table_name"] == table_lowered]
        row = df_slice.iloc[0]
        info["description"] = row["table_description"]
    except (FileNotFoundError, IndexError):
        return error_msg

    data_dict_path = DESCRIPTIONS_DIR / f"{table_lowered}.csv"
    try:
        df = pd.read_csv(data_dict_path)
    except FileNotFoundError:
        return error_msg

    info["columns"] = df["original_column_name"].tolist()
    return info


@mcp.tool()
def get_column_info(database_name: str, table_name: str, column_name: str) -> dict | str:
    """Retrieves information about a given column in dictionary form. Includes its description and data type. If the column doesn't exist, returns an error message."""
    table_lowered = table_name.lower()
    column_lowered = column_name.lower()
    error_msg = f"Error: column {column_name} in table {table_name} in database {database_name} doesn't exist"

    data_dict_path = DESCRIPTIONS_DIR / f"{table_lowered}.csv"
    try:
        df = pd.read_csv(data_dict_path)
    except FileNotFoundError:
        return error_msg

    try:
        df_slice = df[df["original_column_name"] == column_name]
        if len(df_slice) == 0:
            df_slice = df[df["original_column_name"] == column_lowered]
        row = df_slice.iloc[0]
    except IndexError:
        return error_msg

    return {
        "description": row["combined_description"],
        "data_type": row.get("data_format", ""),
    }


@mcp.tool()
def execute_sql(query: str) -> str:
    """Executes a SQL query against the database and returns the result if query execution is successful, else returns the execution error string. If the result is too large, only the first 200 rows are returned."""
    if not DATABASE_PATH.exists():
        return f"Error: database file not found at {DATABASE_PATH}"

    timeout = _query_timeout_seconds()
    try:
        completed = subprocess.run(
            [sys.executable, str(Path(__file__).resolve()), QUERY_WORKER_ARG, str(DATABASE_PATH)],
            input=query,
            capture_output=True,
            text=True,
            timeout=timeout,
            check=False,
        )
    except subprocess.TimeoutExpired:
        return f"Error: query timed out after {timeout:g} seconds"
    except Exception as e:
        return f"Error launching query worker: {e}"

    if completed.returncode != 0:
        detail = completed.stderr.strip() or f"worker exited with status {completed.returncode}"
        return f"Error executing query: {detail}"
    return completed.stdout


@mcp.tool()
def submit_sql(query: str) -> str:
    """Submits the final SQL query for evaluation. If you do not call this tool, the task will be considered incomplete and scored as 0."""
    SUBMISSION_FILE.parent.mkdir(parents=True, exist_ok=True)
    SUBMISSION_FILE.write_text(query)
    return f"Submission received:\n{query}"


if __name__ == "__main__":
    mcp.run(transport="streamable-http", host="0.0.0.0", port=8000)
