# Instructions
You are working in the `european_football_2` database.

Answer the following question:
Among Premier League clubs whose team names reference ports or coastal cities, calculate the average agility attribute for 2014. Consider only players whose favorite language is French and who have a lower center of gravity.

## Additional Context
The following clarifications are provided to help you complete this task:

### The question asks for Premier League clubs "whose team names include references to ports or coastal cities" but does not specify which exact words, phrases, or naming patterns in the database count as port or coastal references.
Team names that include references to ports or coastal cities are identified by matching the following specific team_long_name values in the Team table: 'Portsmouth', 'Plymouth Argyle', 'Southampton', 'Liverpool', 'Manchester City', 'Manchester United', and 'Brighton & Hove Albion'. Use exact matching against these team_long_name values: t.team_long_name IN ('Portsmouth', 'Plymouth Argyle', 'Southampton', 'Liverpool', 'Manchester City', 'Manchester United', 'Brighton & Hove Albion').

### The question asks to consider only players "who have a lower center of gravity," but the business information does not define what qualifies as a "lower center of gravity" or how to identify such players in the database.
Players with a lower center of gravity are defined as those with a height lower than 173 cm. Filter for players where height < 173.

### The Player table contains a favorite_language column with single-letter coded values (C, E, W, XI, O) but the column description does not explain what language each code represents. It is unclear which code corresponds to French-speaking players when filtering for players whose favorite language is French.

The favorite_language column uses coded values where each code represents a different language group. French-speaking players are identified by the code 'E'. Filter for players where favorite_language = 'E' to identify French-speaking players.

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
