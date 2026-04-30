# Instructions
You are working in the `european_football_2` database.

Answer the following question:
From the teams that won exactly 10 games in the 2014/2015 season and are from West European leagues, I want to find the top-10 best teams in that season and list their long name and inscription date. When calculating the top 10, only consider teams with an average effective goals higher than 0.5 in the season. As a start, only consider teams that won exactly 12 games in the season.

Order the results by showing the best teams first, and in case of ties, order by the team's long name in descending alphabetical order.

# Available Commands
The following commands are installed in this terminal — run them directly from the shell.
**Only run ONE command per turn** — each command blocks until the MCP server responds.
- `get_database_info european_football_2` — list all tables and their descriptions
- `get_table_info european_football_2 <table>` — list columns and descriptions for a table
- `get_column_info european_football_2 <table> <column>` — get details for a specific column
- `get_business_info european_football_2 "<question>"` — semantic search over business documentation
- `execute_sql "<query>"` — execute a SQL query against the database
- `submit_sql "<query>"` — submit your final SQL answer

# Submission Instructions
When you are confident your SQL query is correct, call the `submit_sql` tool with your final query as the argument. If you do not call `submit_sql`, the task will be considered incomplete and scored as 0.
