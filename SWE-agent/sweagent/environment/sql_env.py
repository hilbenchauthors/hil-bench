import shutil
import sqlite3
import tempfile
import traceback
from pathlib import Path
from typing import Self

import pandas as pd
from pydantic import BaseModel
from sweagent.environment.hooks.abstract import CombinedEnvHooks, EnvHook


class SQLiteEnvironmentConfig(BaseModel):
    database_type: str = "sqlite"
    name: str = "main"
    max_rows: int = 200
    database_name: str
    base_db_path: str
    working_db_path: str = ""  # If empty, a temporary file will be used
    diff_queries: list[str] = []


SQLEnvironmentConfig = SQLiteEnvironmentConfig


class SQLEnv:
    """
    Represents the SQL environment. It manages the database connection and
    executes SQL queries.
    """

    def __init__(self, config: SQLEnvironmentConfig):
        self.base_db_path = Path(config.base_db_path)
        self._config_working_db_path = config.working_db_path
        self._temp_file_path: Path | None = None
        self.working_db_path: str = ""
        self.database_name = config.database_name
        self.max_rows = config.max_rows
        self.name = config.name
        self.diff_queries = config.diff_queries
        self.conn = None
        self._chook = CombinedEnvHooks()

    @classmethod
    def from_config(cls, config: SQLEnvironmentConfig) -> Self:
        config = config.model_copy(deep=True)
        return cls(config=config)

    def add_hook(self, hook: EnvHook) -> None:
        hook.on_init(env=self)
        self._chook.add_hook(hook)

    def start(self) -> None:
        try:
            # store a copy of the db so the agent can modify it without issue; put in tmp
            # dir unless specific path provided
            if self._config_working_db_path:
                working_db_path = Path(self._config_working_db_path)
                working_db_path.parent.mkdir(parents=True, exist_ok=True)
            else:
                temp_file = tempfile.NamedTemporaryFile(
                    suffix=".sqlite", prefix=f"{self.database_name}_", delete=False
                )
                self._temp_file_path = Path(temp_file.name)
                working_db_path = self._temp_file_path
                temp_file.close()  # Close so sqlite can use it

            shutil.copy(self.base_db_path, working_db_path)
            self.working_db_path = str(working_db_path)
            self.conn = sqlite3.connect(working_db_path, check_same_thread=False)
            if self.diff_queries:
                self._apply_diff_queries()
            print("Connection to SQLite database established successfully.")
        except Exception as e:
            print(f"Error starting SQLite environment: {e}\n{traceback.format_exc()}")

    def _apply_diff_queries(self) -> None:
        cursor = self.conn.cursor()
        for query in self.diff_queries:
            query = query.strip()
            if not query or query.startswith("--"):
                continue
            cursor.execute(query)
        self.conn.commit()

    def close(self) -> None:
        if self.conn:
            self.conn.close()
        self.conn = None
        if self._temp_file_path:
            try:
                self._temp_file_path.unlink()
            except OSError:
                pass  # Best effort cleanup
            self._temp_file_path = None

    def reset(self) -> None:
        self.close()
        self.start()

    def execute_query(self, query: str) -> str:
        if not self.conn:
            return "Error: SQLite database connection is not established."
        try:
            if query.strip().lower().startswith("select"):
                df = pd.read_sql_query(query, self.conn)
                if df.empty:
                    return "Query executed successfully. No results returned."
                if len(df) > self.max_rows:
                    df = df.head(self.max_rows)
                    obs = f"Query executed successfully. Result truncated to the first {self.max_rows} rows.\n"
                else:
                    obs = "Query executed successfully.\n"
                obs += df.to_csv(index=False)
                return obs
            else:
                cursor = self.conn.cursor()
                cursor.execute(query)
                self.conn.commit()
                return f"Query executed successfully. {cursor.rowcount} rows affected."
        except Exception as e:
            return f"Error executing query: {e}"
