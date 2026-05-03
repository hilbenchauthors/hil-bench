# Instructions
You are working in the `financial` database.

Answer the following question:
List the disposition types of loan-eligible accounts located in western districts (order in descending alphabetical order). Only consider districts where the unemployment rate exceeds 4% and the account has a loan with problematic repayment indicators issued in the recent period.

# Available Commands
The following commands are installed in this terminal — run them directly from the shell.
**Only run ONE command per turn** — each command blocks until the MCP server responds.
- `get_database_info financial` — list all tables and their descriptions
- `get_table_info financial <table>` — list columns and descriptions for a table
- `get_column_info financial <table> <column>` — get details for a specific column
- `get_business_info financial "<question>"` — semantic search over business documentation
- `execute_sql "<query>"` — execute a SQL query against the database
- `ask_human "<question>"` — ask a specific clarifying question about a task blocker
- `submit_sql "<query>"` — submit your final SQL answer

# Submission Instructions
When you are confident your SQL query is correct, call the `submit_sql` tool with your final query as the argument. If you do not call `submit_sql`, the task will be considered incomplete and scored as 0.
