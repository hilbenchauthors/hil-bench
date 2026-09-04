# Instructions
You are working in the `formula_1` database.

Answer the following question:
For the youngest driver who made at least one routine pit stop in their debut race weekend, how many "quick" routine pit stops did they make in that debut race, and what was their fastest lap time in that race? Please return the driver's name, race year, race name, date, start time, number of quick routine pit stops, and fastest lap time.

## Additional Context
The following clarifications are provided to help you complete this task:

### The phrase "routine pit stop" is ambiguous because the `pitStops.stop_condition` column contains six distinct code values ('1' through '6'), and it is unclear which subset of these values qualifies as a "routine" pit stop.
A "routine" pit stop is one where `pitStops.stop_condition` is '3' or '6'. Pit stops with any other stop_condition value ('1', '2', '4', or '5') are not considered routine and must be excluded.

### The database does not define what duration qualifies as a “quick pit stop,” so a numeric threshold is missing. Without a specified threshold (and whether the cutoff is inclusive), the count of “quick pit stops” is not determinable.
Define a “quick pit stop” as a pit stop with pitStops.milliseconds less than or equal to 26000 (i.e., pitStops.milliseconds <= 26000). If pitStops.milliseconds is NULL, that pit stop is not considered “quick.”

### The `results.fastestLapTime` column is described as "lap performance timing delta relative to session benchmark," creating ambiguity about whether stored values are absolute lap clock times, session-relative offsets, gap-to-leader deltas, or normalized performance indices.
The `results.fastestLapTime` column stores a processed race-summary metric that does not correspond to any actual recorded lap time. The driver's true fastest lap time should be derived from the `lapTimes` table by selecting the `time` value with the minimum `milliseconds` for that driver and race.

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
