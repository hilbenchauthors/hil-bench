# Instructions
You are working in the `formula_1` database.

Answer the following question:
I want to put together a survey of northern places that hosted races from 2028/01/01 to 2028/06/01 (inclusive), covering the racers who participated in them and whether or not the locations are worth visiting.

Give me each circuit's name, location, if it is a good place to visit (in a column with "Yes" or "No"), the name of the winner, their average lap time, and their balanced average lap time for that race. Also, for comparison, add a column displaying the current average lap time of Verstappen. Only consider locations with a latitude lower than -24 and order the results by circuit name in ascending order.

## Additional Context
The following clarifications are provided to help you complete this task:

### The prompt requires to use the current average lap time of Verstappen, which cannot be known unless searched for.

The current average lap time of Verstappen is 88792 milliseconds

### The prompt first asks for northern places, but then requests to only consider latitudes lower than -24, which is contradictory.

The phrase "latitude lower than -24" uses "lower" directionally (south on a map). Combined with "northern places", filter for circuits with lat > 24.

### The prompt asks for a period of time that starts in 2028, a year that is impossible as it doesn't exist yet and is not found in the data.
The date range for races is from 2008/01/01 to 2008/06/01 (inclusive).

### The "balanced average lap time" is used in the prompt and is mentioned in the business information, but the exact formula is not specified.

The balanced average lap time is calculated as SUM((lap_time / lap_number) * 2.0) / COUNT(*), using decimal division (not integer division).

### To know which place is good to visit, the table called 'location_to_visit' does not have a proper definition of how to be used, since many columns provide similar information.
To know which place is good to visit, the column top from the table location_to_visit should be used, having the value 'V'.

# Available Commands
The following commands are installed in this terminal — run them directly from the shell.
**Only run ONE command per turn** — each command blocks until the MCP server responds.
- `get_database_info formula_1` — list all tables and their descriptions
- `get_table_info formula_1 <table>` — list columns and descriptions for a table
- `get_column_info formula_1 <table> <column>` — get details for a specific column
- `get_business_info formula_1 "<question>"` — semantic search over business documentation
- `execute_sql "<query>"` — execute a SQL query against the database
- `submit_sql "<query>"` — submit your final SQL answer

# Submission Instructions
When you are confident your SQL query is correct, call the `submit_sql` tool with your final query as the argument. If you do not call `submit_sql`, the task will be considered incomplete and scored as 0.
