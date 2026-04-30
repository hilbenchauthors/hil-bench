# Instructions
You are working in the `european_football_2` database.

Answer the following question:
How many high-scoring matches were there in the Belgian Jupiler League in spring 2009, where the home team was favored and played with aggressive defensive tactics,  for teams still in Belgium's top division today, and what is the home dominance ratio?

## Additional Context
The following clarifications are provided to help you complete this task:

### It's unclear which months "spring" refers to and whether "2009" means the 2008/2009 or 2009/2010 season. 
Spring refers to March, April, May. 2009 refers to the spring period within the 2008/09 season.

### It's unclear which values in the defence Aggression column corresponds to "aggressive" defensive tactics - the column contains "Press", "Double", and "Contain", but it's not clear which represents aggressive play.
Aggressive defensive tactics correspond to defenceAggressionClass = "Double"

### The query requires knowledge of which teams are currently in Belgium's top division for the 2025/26 season, which cannot be determined from the database.
The teams from the dataset who are currently in the Belgian top division are: Club Brugge KV, RSC Anderlecht, KAA Gent, KRC Genk, Standard de Liege, Sporting Charleroi, KV Mechelen, SV Zulte-Waregem, KVC Westerlo, KSV Cercle Brugge, Oud-Heverlee Leuven, Sint-Truidense VV,  and FCV Dender EH.

### The term "Home dominance ratio" is not defined in the business information.
Home dominance ratio is the percentage of total goals scored by home teams, calculated as SUM(home_team_goal) * 100.0 / SUM(home_team_goal) + SUM(away_team_goal), rounded to one decimal place.

### The columns B365H, B365D, B365A, and similar, have descriptions like "Match Performance Indicator), that don't explain they are betting odds, or how to determine if a team was favored.
B365H, B365D, and B365A are Bet365 betting odds for Home win, Draw, and Away win, respectively. Lower odds indicate a higher probability. A home team is favored when B365H < B365A (home odds are lower than away odds).

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
