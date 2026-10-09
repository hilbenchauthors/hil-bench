# Instructions
You are working in the `thrombosis_prediction` database.

Answer the following question:
Can you provide the ID, sex, and birthday of older patients under 30 years old, have urea nitrogen just within the borderline of passing, are enrolled in the core monitoring program, and whose laboratory records fall within the standard evaluation period?

## Additional Context
The following clarifications are provided to help you complete this task:

### The question asks for patients “under 30 years old” who are also “older patients,” which is contradictory.
Use an “older patient” as a patient whose time in the system is ≥ 180 days, measured as the difference between Laboratory.Date and Patient.[First Date].

### The term "core monitoring program" is referenced in the question but is not defined in the provided business information or database descriptions.
Patients enrolled in the core monitoring program are defined as those who have more than one laboratory record.

### The definition of "standard evaluation period" is provided but does not specify an exact timeframe that can be directly applied to the data.
The standard evaluation period is defined as laboratory records dated within the calendar year 1994.

# Available Commands
The following commands are installed in this terminal — run them directly from the shell.
**Only run ONE command per turn** — each command blocks until the MCP server responds.
- `get_database_info thrombosis_prediction` — list all tables and their descriptions
- `get_table_info thrombosis_prediction <table>` — list columns and descriptions for a table
- `get_column_info thrombosis_prediction <table> <column>` — get details for a specific column
- `get_business_info thrombosis_prediction "<question>"` — semantic search over business documentation
- `execute_sql "<query>"` — execute a SQL query against the database
- `submit_sql "<query>"` — submit your final SQL answer

# Submission Instructions
When you are confident your SQL query is correct, call the `submit_sql` tool with your final query as the argument. If you do not call `submit_sql`, the task will be considered incomplete and scored as 0.
