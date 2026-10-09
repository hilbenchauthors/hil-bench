# Instructions
You are working in the `formula_1` database.

Answer the following question:
Provide the latitude and longitude of circuits located in Middle Eastern countries that qualify as technical circuits. Consider only circuits that classify for the Russell-Antonelli competitive index, have a premier performance classification, and hosted at least one race with a landslide victory ratio.

## Additional Context
The following clarifications are provided to help you complete this task:

### The question asks for "Middle Eastern Circuits" but it's unclear which countries are considered Middle Eastern for this purpose, as the geographic definition of the Middle East varies.
Filter for circuits where circuits.country is equal to 'UAE' AND 'Bahrain' to identify Middle Eastern circuits.

### The business information defines a technical circuit a slow circuit but it could refer to multiple values like lap time, lap speed, total time, etc and the thresholds to define 'low' are not defined.
Calculate technical circuits using: result.fastestLapSpeed < 192

### It's unclear what is meant by "landslide victory ratio" or how this metric is calculated as it is not specified in the schema or business information.
Using the results table: ((res2.milliseconds − res1.milliseconds) / res1.milliseconds) × 100. Classify a race as a landslide victory when the resulting ratio exceeds 0.35%.

### The business information states that "The Russell-Antonelli competitive index identifies circuits with limited winner diversity." which is vague and doesn't specify how to compute the metric, thresholds or time periods.
To compute the Russell-Antonelli competitive index: retrieve each unique driver ID in the results.positionOrder = 1 and identify circuits that have less or equal than 5 unique winners.

### It's unclear which column in the circuit_performance_table should be used to identify premier performance classification, as there are eight columns that show different circuit-related performance aspects.
Use the column circuit_performance.driver_performance and filter for the value premier.

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
