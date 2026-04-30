# Instructions
You are working in the `european_football_2` database.

Answer the following question:
Create a SQL query that returns exactly 10 rows of the biggest players. Each row must represent a unique player who appeared as home_player_1 in at least one match. A player is eligible if, they are from the golden years of football and they appeared as home_player_1 for at least one team to have given a press conference over the last year. For each eligible player, calculate their condensed body shape and rank globally in descending order by this value. In case of ties, order by player_name in descending alphabetical order. Show me only their names and their team's complete name. Do not aggregate, rank, or arbitrarily select a team for a player; the team shown must come from a specific qualifying match row.


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
