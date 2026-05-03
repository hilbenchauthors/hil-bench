# Instructions
You are working in the `european_football_2` database.

Answer the following question:
Which teams from the England League finished both at the top and bottom three positions of the table in 2016 with high offensive performance, ranked by their top-tier competitive status for that season? Return team name and rank.

## Additional Context
The following clarifications are provided to help you complete this task:

### The question asks for teams that finished "both at the top and bottom of the table" simultaneously, which is logically impossible as a team cannot occupy two mutually exclusive positions at the same time.
Only look for the top-3 positions (ranks 1-3).

### The term "table" is ambiguous and can be interpreted as home table (only home matches), away table (only away matches), or overall standings (combined home and away results). Each interpretation yields different team rankings.
Interpret "table" as the home standings table, considering only matches played at home venue to calculate points, goals, and positions.

### The term "high offensive performance" lacks specific criteria. No threshold value, metric definition (goals scored, shots on target, possession in attacking third), or comparison baseline (league average, historical data) is provided.
Define "high offensive performance" as teams with 35 or more goals scored in matches during the season, based on available goal data in the Match table. Apply high offensive performance filter before any ranking.

### The question requires ranking teams by “top-tier competitive status,” but this is a business-specific metric that is not defined anywhere.
The "Top-tier competitive status" should be calculated as the relative ranking based on goals scored then ranked by  goal difference and then by match points Final tie break should be by alphabetical order.

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
