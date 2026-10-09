# Instructions
You are working in the `european_football_2` database.

Answer the following question:
List the names and overall adjusted ratings of short players in Western European leagues with strong volley and dribbling scores. If a player appears multiple times, show only the entry with the highest overall rating.


## Additional Context
The following clarifications are provided to help you complete this task:

### The question asks for "short players" but this term can be interpreted in multiple ways. It is unclear whether "short" refers to players below average height, players below a specific height threshold (such as 170cm, 175cm, or 180cm), or the shortest players in the dataset (bottom percentile).
Short players refers to players with height less than 173cm. Filter for players where height < 173.

### The question asks for players in "Western European leagues" but this geographic term is not precisely defined. It is unclear which specific countries or leagues qualify as Western European, as different definitions may include or exclude countries like the United Kingdom, Germany, Belgium, Netherlands, and others.



Western European leagues refers to leagues from Spain, Italy, France, and Portugal. Filter for leagues where the country name is in ('Spain', 'Italy', 'France', 'Portugal').

### The business information defines "strong volley and dribbling scores" as "player performance metrics demonstrating elevated technical proficiency levels in ball striking and ball manipulation capabilities, reflecting superior skill execution standards relative to baseline assessment criteria," but this definition is vague and does not specify the actual threshold values or numeric criteria for determining strong scores.
Strong volley and dribbling scores means volley score > 75 AND dribbling score > 77. Filter for players where volleys > 75 AND dribbling > 77.

### The Player_Attributes table contains multiple rating columns (Rating1, Rating2, Rating3, Rating4, Rating5, Rating6, Rating7) all described as "player performance assessment metric," but the table definition does not clearly explain what each rating represents or which rating column should be used for filtering by overall rating. The table's multi-rating structure with seven similar columns is confusing and makes it unclear which column captures the player's overall FIFA rating.

Rating2 represents the player's overall adjusted FIFA rating. Use Rating2 to filter and display players' overall adjusted ratings.

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
