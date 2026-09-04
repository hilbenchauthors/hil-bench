# Instructions
You are working in the `california_schools` database.

Answer the following question:
Please list the codes of the schools with an effective grade higher than 8, a sat math score higher than 450, and a total enrollment higher than the average enrollment per school in Argentina in 2024.

## Additional Context
The following clarifications are provided to help you complete this task:

### The SAT math scores column ("AvgScr3") contains the "OOC" value, which is unclear.
The "OOC" value in the SAT math scores column ("AvgScr3") means "Out Of Charts" and should be considered as higher than 450.

### The "effective grade" term was included as "the average between the high and low grade", but does not describe how to handle non-numeric values in the column.

Non-numeric values for effective grade should be excluded.

### The prompt asks for the average sat score in math, but the table only has column with names "AvgScr1", "AvgScr2", and "AvgScr3".

The column "AvgScr3" corresponds to the average SAT score in math.

### The prompt asks for a total enrollment higher than the average enrollment per school in Argentina in 2024, which can only be found by browsing.

The value 897 should be used as the average enrollment per school in Argentina in 2024.

# Available Commands
The following commands are installed in this terminal — run them directly from the shell.
**Only run ONE command per turn** — each command blocks until the MCP server responds.
- `get_database_info california_schools` — list all tables and their descriptions
- `get_table_info california_schools <table>` — list columns and descriptions for a table
- `get_column_info california_schools <table> <column>` — get details for a specific column
- `get_business_info california_schools "<question>"` — semantic search over business documentation
- `execute_sql "<query>"` — execute a SQL query against the database
- `submit_sql "<query>"` — submit your final SQL answer

# Submission Instructions
When you are confident your SQL query is correct, call the `submit_sql` tool with your final query as the argument. If you do not call `submit_sql`, the task will be considered incomplete and scored as 0.
