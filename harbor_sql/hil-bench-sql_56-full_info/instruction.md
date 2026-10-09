# Instructions
You are working in the `california_schools` database.

Answer the following question:
Among schools opened in the early 2000s that have active district status, which five schools have the lowest average scores in the most important subject for humanities degrees, and what are their telephone numbers?

## Additional Context
The following clarifications are provided to help you complete this task:

### The question asks for schools opened in "the early 2000s" but does not specify how many years constitute "early." It is unclear whether this means 2000-2004, 2000-2007, 2000-2010, or another range within the decade.
"Early 2000s" means 2000 through 2004 inclusive. Filter for schools where OpenDate is between '2000-01-01' and '2004-12-31'.

### The question asks for average scores in "the most important subject for humanities degrees" but the business information does not define which subject this refers to. It is unclear whether this means Reading, Writing, or another subject area.
The most important subject for humanities degrees is Reading. Filter for schools based on their AvgScrRead (average scores in Reading) from the satscores table.

### The StatusType column in the schools table contains numeric codes (1, 2, 3, 4) without clear explanations of what each code represents. It is unclear which numeric value corresponds to "active district status" when filtering schools.
In the StatusType column, the value 1 represents Active status. Filter for schools where StatusType = 1 to identify schools with active district status.

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
