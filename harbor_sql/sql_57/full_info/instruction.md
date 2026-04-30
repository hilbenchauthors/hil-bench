# Instructions
You are working in the `european_football_2` database.

Answer the following question:
I need to compare Aaron Lennon and Abdelaziz Barrada. Which of them had a rating above 150 points when they were at the peak of their career? For that player, tell me his net worth, assuming each performance point is equivalent to U$D 10,000, and display it alongside Julian Alvarez's net worth in the same row.

## Additional Context
The following clarifications are provided to help you complete this task:

### The question asks for players with a rating above 150 points, but player ratings in the database use a 0-100 scale, making this requirement impossible to satisfy.
Look for a rating greater than 95 instead of 150.

### The prompt requires to use Julian Alvarez's net worth, which can not be known unless searched for.

Julian Alvarez's net worth is U$D 20 millon

### The business information defines "career peak" as when "performance adequately reflects footballing maturity," but this definition is vague and does not specify which metrics or thresholds to use.
A player is at their career peak when their overall_rating is greater than or equal to their potential.

### There are many columns containing player rating information: overall_rating_1, overall_rating_2, overall_rating_3, potential, career_rating, and career_potential. It is unclear which should be used to evaluate player performance.
Use the columns overall_rating_3 and potential from the Player_Attributes table.

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
