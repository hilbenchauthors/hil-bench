# Instructions
You are working in the `european_football_2` database.

Answer the following question:
From the teams that won exactly 10 games in the 2014/2015 season and are from West European leagues, I want to find the top-10 best teams in that season and list their long name and inscription date. When calculating the top 10, only consider teams with an average effective goals higher than 0.5 in the season. As a start, only consider teams that won exactly 12 games in the season.

Order the results by showing the best teams first, and in case of ties, order by the team's long name in descending alphabetical order.

## Additional Context
The following clarifications are provided to help you complete this task:

### The prompt first asks for teams who won exactly 10 matches, but then requests that they won exactly 12 matches, which is contradictory.

Consider teams that won between 10 and 12 matches in the season (inclusive).

### The prompt asks for the "best" teams, which can be interpreted either by final position, highest number of goals done, lowest number of goals received, etc.

When looking for the "best" teams, use the lowest number of goals received in a season.

### The prompt asks for "west European leagues", which makes it unclear which countries to include

Consider the countries Poland, Scotland, Switzerland, Netherlands, and Germany for west european leagues. Considering any other teams would result in an incorrect answer.

### The "average effective goals" is used in the prompt and is mentioned in the business information as a weighted average between the home and away goals, but the weights are not specified.

The average effective goals from a season can be calculated as (home_goals_in_the_season*0.3 + away_goals_in_the_season*0.7)/number_of_matches_in_the_season

### The Team table has 4 columns with similar names, which makes it impossible to know which one refers to the inscription date.

The team's inscription date is given by the "important_date" column of the Team table.

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
