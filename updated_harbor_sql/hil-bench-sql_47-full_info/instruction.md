# Instructions
You are working in the `california_schools` database.

Answer the following question:
Among the small, recently opened schools with a low academic readiness index, how many low-performing schools in SAT are exclusively virtual?

## Additional Context
The following clarifications are provided to help you complete this task:

### It is unclear what a "low-performing school in SAT" is, which could refer to average math scores, reading scores, or excellence rate. 
A low-performing school is one where the average SAT math score is less than 550.

### The term "small schools"  is vague and does not specify a threshold.
A small school is one with an enrollment in grade 12 (enroll12) of a maximum of 30 students.

### The term "recently opened" does not specify a date range or cutoff for when a school must have opened.
A recently opened school is one with an OpenDate on or after January 1, 1990.

### The term "academic readiness index" is not defined anywhere in the business information or database schema.
The academic readiness index is calculated as the number of SAT test takers (NumTstTkr) divided by the 12th-grade enrollment (enroll12). A "low" academic readiness index is lower than 0.8.

### The virtual column contains single-letter codes (F, V, C, N, P), but their meanings are not explained in the column description.
A school that is exclusively virtual has a value of "F" in the virtual column.

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
