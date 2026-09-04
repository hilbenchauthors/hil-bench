# Instructions
You are working in the `formula_1` database.

Answer the following question:
For the 2017 season, list the sum of Verified Constructor Points per constructor for all races held at classic circuits that featured at least one standard pit stop.

## Additional Context
The following clarifications are provided to help you complete this task:

### The term "classic circuits" is subjective and lacks a standardized definition or specific list in the database or business context, preventing the creation of a filter for the circuits table.
Classic circuits are defined specifically and explicitly as 'monaco', 'silverstone', 'spa', 'monza', and 'suzuka'.

### The business definition of "optimal duration window" is vague and fails to provide the specific numerical bounds (in milliseconds) required to filter the pitStops table.
A standard pit stop is defined as having a duration between 18,250 and 24,890 milliseconds.

### The term "verified constructor points" creates an ambiguity in the schema since there are multiple tracking columns in constructorResults (logs, audit_tracking, verified_logs) but it is unclear how to calculate the verified constructor points from these columns.
Verified constructor points should be calculated as the sum of verified_logs plus half of logs. The formula is: COALESCE(verified_logs, 0) + (logs / 2.0)

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
