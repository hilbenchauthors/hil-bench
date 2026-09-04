# Instructions
You are working in the `california_schools` database.

Answer the following question:
I want to compare the Western counties to find out which one offers the most schools that do not offer virtual classes and are administrated in an elementary school district. Indicate the total amount for Alpine and Amador, showing both of them in descending order. Do a simple COUNT() of the schools matching the filter results for total amount. Exclude schools with count = 0.

## Additional Context
The following clarifications are provided to help you complete this task:

### The prompt asks for western counties, but Alpine and Amador are eastern counties.
Comparing western counties is the purpose of the prompt. Only look for the San Diego and Santa Barbara counties.

### The question asks about schools in administrated in an elementary school district but this is not clear what this means and should be defined in the business info.
Schools administrated in an elementary school district have DOC = '52'. It should not use DOCType = 'Elementary School District'

### The InstructionType column in the schools table contains coded values (T, U, W, X, Y) without explanations of what each code represents. It is unclear which value or values correspond to schools that do not offer virtual classes.
In the InstructionType column of the table schools, the code 'T' represents schools that do not offer virtual classes. The column name is exactly "InstructionType".

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
