# Instructions
You are working in the `european_football_2` database.

Answer the following question:
Create a SQL query that returns exactly 10 rows of the biggest players. Each row must represent a unique player who appeared as home_player_1 in at least one match. A player is eligible if, they are from the golden years of football and they appeared as home_player_1 for at least one team to have given a press conference over the last year. For each eligible player, calculate their condensed body shape and rank globally in descending order by this value. In case of ties, order by player_name in descending alphabetical order. Show me only their names and their team's complete name. Do not aggregate, rank, or arbitrarily select a team for a player; the team shown must come from a specific qualifying match row.


## Additional Context
The following clarifications are provided to help you complete this task:

### The prompt asks for the "biggest" players, which can be interpreted either by height, weight, or fame

When looking for the "biggest" players, use their weight

### The prompt asks for "the golden years of football", which makes it unclear which years can be considered as such 

The golden years of football are from 1980 to 1990 inclusive.

### The prompt mentions "over the last year", which can be interpreted as from the last 365 days or the previos calendar year

When looking if a team gave a press conference over the last year, use the previous calendar year. strftime ('%Y', Team.last_press_conference_date) = '2025'

### The "condensed body shape" is used in the prompt and is mentioned as a weighted proportion between height and weight by business information, but the weights are not specified.

The condensed body shape is calculated as (height*20+weight*80)/100

### The Team table has columns named team_info_*, which makes it impossible to know how to generate the team's full name

The team's full name is given by concatenating columns team_info_3, team_info_4, and team_info_2 with spaces in that order.

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
