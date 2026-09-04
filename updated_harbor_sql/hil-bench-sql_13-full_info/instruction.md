# Instructions
You are working in the `european_football_2` database.

Answer the following question:
Can you list the players who are clinical in front of goal who play for teams currently competing in the UEFA champions league with a disciplined playstyle at eligible match venues in Serie A's 128th league season? Please return the player's name, team name, and venue tier.

## Additional Context
The following clarifications are provided to help you complete this task:

### Which clubs are currently competing in the UEFA Champions League is real time information and can't be determined from the dataset. 
The teams currently competing in the UEFA Champions League are Napoli, Inter, Atalanta, and Juventus.

### The question asks for data from the 128th Serie A season, but Serie A has only had approximately 124 seasons to date, so this season has not yet occurred in real life.
Use the 2011/12 Serie A season. For attribute tables, filter for the exact season between '2011-08-01' AND pa.date <= '2012-06-01'

### It's unclear what values determine if a player is "clinical in front of goal" and there is no business information to address this.
Players are clinical in front of goal if they have Finishing >= 83 AND Shot Power >= 80.

### It's unclear what is meant by a "disciplined playstyle" and there is no business information to address this.
The term "disciplined playstyle" refers to teams with a controlled defensive structure. This is: Defence Pressure Class = 'Medium', Defence Defender Line Class = 'Cover', Build Up Play Speed Class = 'Balanced', defencePressure <=50 and buildUpPlayPassing >= 45.

### The venue_ops_tier column in the Match table contains single-letter coded values ('K', 'M', 'R', 'P') but the schema describes it only as 'A venue's category' without documenting what each code represents, making it impossible to determine which code corresponds to which venue classification.
In the venue_ops_tier column, 'K' represents the standard operational tier (eligible match venues), 'M' represents managed facilities, 'R' represents restricted venues, and 'P' represents provisional venues.

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
