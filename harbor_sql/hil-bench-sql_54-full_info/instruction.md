# Instructions
You are working in the `european_football_2` database.

Answer the following question:
List the players who are shorter than 175cm who have been assessed with an overall rating no more than 80 and elite shooting capabilities, and with an overall rating between 82 and 90. Consider only players who have played any game in the England Premier League, Italy Serie A, or Spain LIGA BBVA, with low injury risk. Order the results alphabetically by player name.

## Additional Context
The following clarifications are provided to help you complete this task:

### The question mentions "overall rating" twice with mutually exclusive conditions (≤ 80 and between 82-90). Player_Attributes contains several rating-like columns (overall_rating, potential, international_reputation, overall_performance), making it ambiguous which column the second "overall rating" refers to.
The first "overall rating no more than 80" refers to overall_rating. The second "overall rating between 82 and 90" refers to the potential column. Filter using: WHERE pa.overall_rating <= 80
  AND pa.potential BETWEEN 82 AND 90

### The question asks for players with "elite shooting capabilities," but this term is not defined anywhere in the business information.
Elite shooting capabilities are defined as having an average of finishing, heading_accuracy, volleys, and curve greater than 75. Calculate using: WHERE (pa.finishing + pa.heading_accuracy + pa.volleys + pa.curve) / 4.0 > 75

### The question asks for players with "low injury risk," but the Player table's injury_prone column uses opaque coded values (Q1, Q2, Q3, Q4, Outlier) with no documentation explaining which code indicates low risk.
Players with low injury risk have injury_prone = 'Q3'. Filter using: WHERE p.injury_prone = 'Q3'

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
