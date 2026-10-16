# Instructions
You are working in the `european_football_2` database.

Answer the following question:
Who was the winner of the standout match on November 31, 2008, where the home team won with no goals scored? Also give me the final score, alongside the most common score in the Argentina League for 2025. 

## Additional Context
The following clarifications are provided to help you complete this task:

### The prompt requires to use the most common score in the Argentina League for 2025, which can not be known unless searched for

The most common score in the Argentina League for 2025 is 2-1 (2 home goals, 1 away goals)

### The question asks for a match on November 31, 2008, but November only has 30 days, making this date impossible.
Look for a match on November 22, 2008.

### The question asks for a match where the home team won with no goals scored which is logically impossible as a 0 - 0 match is a draw.
The user meant that the away team scored fewer goals and at least 1 goal.

### The business info states "A standout match refers to games with exceptional circumstances" but does not define what "exceptional circumstances" means.
A standout match is the match where the home team was the strongest favorite, indicated by the lowest B365H odds value.

### The database has many columns with scores. The Match table with home_team_goal_results_1/away_team_goal_results_1, 2, and 3 columns from an external provider, and the League_Results table with home_goals/away_goals columns, recorded by the league. Some matches show different scores between tables. It is unclear which table contains the verified final scores.
Use the columns home_team_goal_results_2 and away_team_goal_results_2 from the Match table for official match scores.

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
