# Instructions
You are working in the `california_schools` database.

Answer the following question:
How many grant-eligible schools that have students enrolled to FRPM in grades ranging from Kindergarten through 8th grade across all academic years? List each city along with the count of qualifying schools and also include the number of magnet schools currently active in the same city.

## Additional Context
The following clarifications are provided to help you complete this task:

### The question request the number of active magnet schools as of today but there's no recent information included in the dataset.
Count schools with schools.magnet = 1 and schools.StatusType = Active with frpm.Academic Year in the year 2016.

### The question refers to a "grant-eligible schools", but does not define what qualifies as "grant-eligible".
Consider schools "grant-eligible" when frpm.Percent (%) Eligible FRPM (K-12) is equal or higher than 0.5 and frpm.Percent (%) Eligible FRPM (Ages 5-17) is equal or higher than 0.5.

### The column GSserved represents the enrollment but the values in the column are unclear.
Filter for schools.GSserved values equal to 'P'

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
