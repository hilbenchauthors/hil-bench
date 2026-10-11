# Instructions
You are working in the `california_schools` database.

Answer the following question:
List the names of the first 5 schools, alphabetically ordered, with institutional email domains that have a literacy index greater than 750 and offer mixed classes.

## Additional Context
The following clarifications are provided to help you complete this task:

### The question asks for schools with "institutional email domains" but it is unclear which email domain suffixes qualify as institutional domains.
Institutional email domains refer to the administrator email addresses (AdmEmail1 column) that end in .k12.ca.us only.

### The question mentions "literacy index" but does not specify how this metric should be calculated from the available SAT score data.
Literacy index is calculated using the formula: (AvgScrRead / 2) + AvgScrWrite.

### The question asks for schools that "offer mixed classes" but the Virtual column contains codes (A, B, C, D, E) without clear definitions, making it unclear which values represent mixed instruction.
Mixed classes refer to schools with Virtual column values B, C, or D only.

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
