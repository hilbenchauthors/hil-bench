# Instructions
You are working in the `formula_1` database.

Answer the following question:
List the top 3 drivers born between 1980 and 1985 with the shortest average pit stop duration per race, considering only pit stops that are regarded as representative of a driver’s typical performance, from races meeting minimum field requirements available in the dataset. Return only the driver’s forename and surname as separate columns, ordered by the shortest average pit stop duration.

## Additional Context
The following clarifications are provided to help you complete this task:

### The question asks for the shortest average pit stop duration per race, but it is unclear how to handle multiple pit stops for the same driver within the same race when computing a driver-level average. Different within-race aggregation rules produce different results.
For each driver and race, exactly one pit stop row is selected: the pit stop whose duration value is closest to the average pit stop duration of that race across all drivers (using the same duration definition as applied to pit stop rows). If multiple pit stops are equally close, select the one with the smallest stop number; if still tied, select the one with the smallest row identifier. The driver’s average equals the arithmetic mean of the selected per-race pit stop durations across all included races. Only drivers with at least one selected per-race pit stop duration are eligible for the top 3 ranking. If multiple eligible drivers have the same average duration, rank them by driverId ascending.

### The question says to consider only pit stops that are representative of typical performance, but the dataset does not specify which pit stops qualify as representative versus atypical.
A pit stop is representative only if it occurs in a race where the driver’s race result has a recorded final position (results.position is not NULL) and a recorded finishing time in milliseconds (results.milliseconds is not NULL). Pit stop rows from races where either value is NULL are excluded.

### The question refers to "races meeting minimum field requirements" but does not define what constitutes minimum field requirements for race eligibility. The business information provides no guidance on what threshold or criteria must be met for a race to qualify.
A race meets minimum field requirements only if the pitStops table contains pit-stop records for at least 10 distinct drivers in that race. Only those races are included in the analysis, regardless of season or year.

### The schema has multiple duration-like fields and unclear definitions, so it is ambiguous how to interpret “pit stop duration” as a single comparable numeric value.
The numeric pit stop duration value in seconds is derived from pitStops.duration. If duration contains :, interpret it as minutes:seconds and compute seconds as 60*minutes + seconds using the substring before and after :. Otherwise, interpret duration directly as seconds using a numeric cast. Rows where duration is NULL or cannot be cast to a number are excluded.

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
