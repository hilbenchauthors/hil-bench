# Instructions
You are working in the `codebase_community` database.

Answer the following question:
List the top 10 verified senior-tier members who have authored the most posts about time series concepts. For each member, report their display name, the number of matching posts, and the total bounty amount in USD awarded on their matching posts, computed as the sum of bounty amounts converted from EUR to USD using today’s EUR/USD exchange rate. Round the USD total to 2 decimal places. Treat “authored posts” as posts created by the user (not edits), and include both questions and answers. Order results by matching post count in descending order, breaking ties by display name in ascending order.

# Available Commands
The following commands are installed in this terminal — run them directly from the shell.
**Only run ONE command per turn** — each command blocks until the MCP server responds.
- `get_database_info codebase_community` — list all tables and their descriptions
- `get_table_info codebase_community <table>` — list columns and descriptions for a table
- `get_column_info codebase_community <table> <column>` — get details for a specific column
- `get_business_info codebase_community "<question>"` — semantic search over business documentation
- `execute_sql "<query>"` — execute a SQL query against the database
- `submit_sql "<query>"` — submit your final SQL answer

# Submission Instructions
When you are confident your SQL query is correct, call the `submit_sql` tool with your final query as the argument. If you do not call `submit_sql`, the task will be considered incomplete and scored as 0.
