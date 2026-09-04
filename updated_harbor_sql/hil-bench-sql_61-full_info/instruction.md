# Instructions
You are working in the `california_schools` database.

Answer the following question:
Who is administering the top 5 northern schools with the best students? For each school, indicate all administrators' full names (with first and last name separated by space) and multiple administrators separated by dots, along with the school's legislative name (in the same row). Only consider active schools.

## Additional Context
The following clarifications are provided to help you complete this task:

### The prompt asks for the schools with the "best" students, which can be interpreted by SAT score in each of the three fields (or their average), NumGE1500 

When looking for the schools with the "best" student, use their average SAT score in math

### The prompt asks for "northern schools", which makes it unclear which schools can be considered as such 

The northern schools are those with a latitude over 37.7.

### The prompt mentions the "legislative name", but it is not explained what this term means.

The "legislative name" is obtained as: "{ZIP}: {State}, {school's name}". 
Only include schools where Zip, State, and School name are not NULL.

### The "StatusType" column in the "schools" table contains values that cannot be interpreted. It is impossible to understand how to use this column to determine whether a school is active or not.

A school is active if the "StatusType" column in the "schools" table contains the values "3", "J", "S", or "T".

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
