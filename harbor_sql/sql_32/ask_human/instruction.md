# Instructions
You are working in the `codebase_community` database.

Answer the following question:
List the display name of elite contributors who posted questions tagged with '<r>' after R version 8.0, whose total bounty earnings exceed the average earned by a professional blogger in a month (in USD), and had at least 3 years of membership tenure when the platform closed ('2014-09-14'). 

Only return each qualifying contributor's display name, ordered alphabetically by display name. Only consider accounts that were created in the last 12 months before the platform closed and that have a level 3 honor status.

# Available Commands
The following commands are installed in this terminal — run them directly from the shell.
**Only run ONE command per turn** — each command blocks until the MCP server responds.
- `get_database_info codebase_community` — list all tables and their descriptions
- `get_table_info codebase_community <table>` — list columns and descriptions for a table
- `get_column_info codebase_community <table> <column>` — get details for a specific column
- `get_business_info codebase_community "<question>"` — semantic search over business documentation
- `execute_sql "<query>"` — execute a SQL query against the database
- `ask_human "<question>"` — ask a specific clarifying question about a task blocker
- `submit_sql "<query>"` — submit your final SQL answer

# Submission Instructions
When you are confident your SQL query is correct, call the `submit_sql` tool with your final query as the argument. If you do not call `submit_sql`, the task will be considered incomplete and scored as 0.
