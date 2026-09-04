# Instructions
You are working in the `european_football_2` database.

Answer the following question:
What are the names of the best attack-effective teams in the past few seasons? Consider only teams that in the 2015/2016 season used a measured build-up play approach and tell me which was their defensive classification in that season, and return only their names and the defensive classification.

## Additional Context
The following clarifications are provided to help you complete this task:

### The question asks for teams with a "measured build-up play approach," but the database contains multiple build-up play metrics covering speed, passing distance, dribbling frequency, and positional structure, each with different categorical values. "Measured build-up play" is not precisely defined and could plausibly refer to any of these dimensions or a combination, and there is no standard definition mapping this term to a specific metric or value.
Filter teams where buildUpPlaySpeedClass = 'Balanced' AND buildUpPlayDribblingClass = 'Little' in the Match.season equal to 2015/2016.

### The phrase "past few seasons" does not specify how many seasons to include. The database contains eight seasons (2008/2009 through 2015/2016), and "few" could reasonably mean 2, 3, 4, or 5 seasons, each producing different performance rankings.
Filter matches where season IN ('2012/2013', '2013/2014', '2014/2015', '2015/2016') (inclusive).

### The term "top attack-effective teams" is vague and could refer to several offensive values to identify top-performing teams.
Top attack-effective teams are defined by computing total goals scored (home_team_goal when home + away_team_goal when away) divided by total matches played. Top attack-effective teams have goals per match greater than 1.5.

### The question asks for a "defensive classification," but the schema provides at least two different tables and several columns that could match the request. Additionally, some columns have contradicting descriptions.
Use the column Team_Attributes.defenceAggressionClass in the season Match.season 2015/2016.

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
