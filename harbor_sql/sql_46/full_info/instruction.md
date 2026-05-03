# Instructions
You are working in the `codebase_community` database.

Answer the following question:
What percentage of our youngest users (in terms of when they joined) were effectively 'Ignored' on their first question, according to the Community Engagement SOP? Only consider users who have special status, have asked at least one question, and are labeled as lowest-tier contributors.

## Additional Context
The following clarifications are provided to help you complete this task:

### The term "youngest users (in terms of when they joined)" is an underspecified concept because it lacks a clear definition of how long ago they should have joined.
Explicitly define "youngest users (in terms of when they joined)" as accounts created between January 1, 2014, and December 31, 2014, inclusive.

### The Community Engagement SOP guidelines required to classify a post as "ignored" are not provided. Without these guidelines, this status cannot be labeled precisely.
The Community Engagement SOP uses the 72-hour rule, where any post without a formal answer within 72 hours of its creation date is categorized as "Ignored".

### The "s_status" column from the users table contains categorical values (S_1 through S_4), but the schema does not define which category maps to "lowest contributors".
The "lowest contributors" are those labeled as "S_3" in the "s_status" column from the users table.

# Available Commands
The following commands are installed in this terminal — run them directly from the shell.
**Only run ONE command per turn** — each command blocks until the MCP server responds.
- `get_database_info codebase_community` — list all tables and their descriptions
- `get_table_info codebase_community <table>` — list columns and descriptions for a table
- `get_column_info codebase_community <table> <column>` — get details for a specific column
- `get_business_info codebase_community "<question>"` — semantic search over business documentation
- `execute_sql "<query>"` — execute a SQL query against the database
- `submit_sql "<query>"` — submit your final SQL answer

# Submission Instructions
When you are confident your SQL query is correct, call the `submit_sql` tool with your final query as the argument. If you do not call `submit_sql`, the task will be considered incomplete and scored as 0.
