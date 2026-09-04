# Instructions
You are working in the `european_football_2` database.

Answer the following question:
What are the player names and average long passing scores for the top 5 players ranked by highest average long passing score who are noted for high attacking effort and whose proficiency index exceeds 80, based on evaluations from the past few years? Only include players with a confirmed roster standing. Order results by average long passing score descending, then by player name ascending. Return exactly two columns: player name and average long passing score.

## Additional Context
The following clarifications are provided to help you complete this task:

### The phrase "past few years" does not specify how many years of evaluations to include. The database spans multiple years, and "few" is inherently vague, producing different player rankings depending on the time window selected.
Filter evaluations where date >= '2015-01-01' AND date < '2017-01-01', covering the two most recent years of data.

### The question refers to players noted for 'high' attacking effort, but the dataset contains multiple distinct categorical labels representing different effort classifications, including several labels near the high-effort tier. The question does not specify which exact labels should be treated as a match.
Filter records where attacking_work_rate IN ('high', 'high_output'), which represent the high-effort classification tier. Other labels like 'high_press' and 'medium_high' should not be included.

### The question references a "proficiency index" threshold, but no definition or formula for this metric is provided anywhere. Multiple player attributes could be used to compute it, and there is no way to determine the correct calculation.
Compute proficiency index per evaluation record as (vision + short_passing + long_passing) / 3.0. Filter to evaluation records where this value exceeds 80, then compute each player’s average long passing as AVG(CAST(long_passing AS REAL)) over the remaining records.

###  The question asks for players with a "confirmed roster standing," and the Player table contains a roster_tag column, but its values are single-letter codes with no documented meaning, making it impossible to determine which code represents a confirmed standing.
Filter players where roster_tag = 'Q'. This value indicates a confirmed roster standing.

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
