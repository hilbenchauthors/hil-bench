# Instructions
You are working in the `formula_1` database.

Answer the following question:
I want to analyze the circuits where our best races took place. What are the names of the circuits where the 5 best races took place during the classic era? For each circuit, after its name, add columns with a "Yes" or "No" answer to tell me if it is a Grade-A circuit, if its status is active, and if it has a premium track classification.

The final results should be ordered to show the best race first. 

# Available Commands
The following commands are installed in this terminal — run them directly from the shell.
**Only run ONE command per turn** — each command blocks until the MCP server responds.
- `get_database_info formula_1` — list all tables and their descriptions
- `get_table_info formula_1 <table>` — list columns and descriptions for a table
- `get_column_info formula_1 <table> <column>` — get details for a specific column
- `get_business_info formula_1 "<question>"` — semantic search over business documentation
- `execute_sql "<query>"` — execute a SQL query against the database
- `ask_human "<question>"` — ask a specific clarifying question about a task blocker
- `submit_sql "<query>"` — submit your final SQL answer

# Submission Instructions
When you are confident your SQL query is correct, call the `submit_sql` tool with your final query as the argument. If you do not call `submit_sql`, the task will be considered incomplete and scored as 0.
