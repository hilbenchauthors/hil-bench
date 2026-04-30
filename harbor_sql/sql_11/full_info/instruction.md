# Instructions
You are working in the `formula_1` database.

Answer the following question:
I want to find the top 10 best drivers who are not married yet. Provide their surname alongside their driver efficiency index.

## Additional Context
The following clarifications are provided to help you complete this task:

### The prompt asks for the "best" drivers, which can be interpreted either by their overall position, how many races they won, or their average lap time

When looking for the "best" drivers, use the lowest lap time they've ever made.

### The term "driver efficiency index" is not defined in the business information or anywhere in the schema. It is unclear how this metric is calculated.

The "driver efficiency index" can be obtained as the average of each race's average lap time in milliseconds, this is, AVG(AVG(milliseconds) per race).

### The prompt requests drivers who are not married yet. The "married" column in the "driver" table contains values that are a mix of text and numbers and can't be easily interpreted.

Drivers who are not married are indicated by the "married" column in the "driver" table having values "L", "C", or 0

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
