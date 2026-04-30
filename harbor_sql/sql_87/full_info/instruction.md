# Instructions
You are working in the `california_schools` database.

Answer the following question:
Among the best northern schools that enroll more than 300 students of ages 5-17, I want to know their corrected SAT scores and whether or not any of them have fewer than 250 students in total. Provide also their name and charter number (if they have one).


## Additional Context
The following clarifications are provided to help you complete this task:

### The prompt first asks for schools that enroll more than 300 students of ages 5-17 and then whether or not any of them have less than 250 students in total, which is contradictory.

The correct action is to for schools that enroll more than 200 students of ages 5-17 and keep looking if any of them have less than 250 students in total.

### The threshold coordinates for defining a school as 'northern' are unclear.

A "northern" school is one with a latitude above 37.7.

### What makes a school one of the "best" can be interpreted as per the SAT scores, free meal count, elegible frpm rate, etc.

The "best" schools, are those with the highest elegible frpm rate.

### The prompt uses the corrected SAT score term, which is mentioned in business information, but how to give more importance to math is not defined.

The corrected SAT score can be calculated as (math*50+read*25+write*25)/100

### The Schools table contains columns code1, code2, and code3, making it impossible to know which one is the charter number

To find the charter number, use the column code3 from the Schools table

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
