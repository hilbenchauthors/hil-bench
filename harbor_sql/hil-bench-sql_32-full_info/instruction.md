# Instructions
You are working in the `codebase_community` database.

Answer the following question:
List the display name of elite contributors who posted questions tagged with '<r>' after R version 8.0, whose total bounty earnings exceed the average earned by a professional blogger in a month (in USD), and had at least 3 years of membership tenure when the platform closed ('2014-09-14'). 

Only return each qualifying contributor's display name, ordered alphabetically by display name. Only consider accounts that were created in the last 12 months before the platform closed and that have a level 3 honor status.

## Additional Context
The following clarifications are provided to help you complete this task:

### The question uses “after the release of R version 8.0” as a time anchor, but no such R version exists, so the intended cutoff date is unclear.
Treat the intended reference as R version 2.10.0, released on 2009-10-26. Thus, filter posts created after 2009-10-26.

### The prompt requires to use the average earned by a professional blogger in a month (in USD), which cannot be known unless searched for.

The average amount earned by a professional blogger in a month (in USD) is 500 USD.

### The request requires at least 3 years of membership tenure while also stating that the account was created in the last 12 months, which cannot both be true without clarifying which time requirement is intended.
Reinterpret '3 years' as '3 months' for consistency. The only conditions to apply to the account's creation date and last access date are that the creation date must be on or before date('2014-09-14', '-3 months'), and the last access date must be on or after date('2014-09-14', '-12 months').

### The question refers to "elite contributors," but neither the business information nor the schema defines what qualifies a user as an elite contributor, and multiple metrics could plausibly be used.
Define an elite contributor as a user with Reputation > 5000.

### The "Honor" column in the "users" table contains values that are not numeric and cannot be interpreted. It is impossible to understand how to use this column to calculate the honor level of a user.

The users with a level 3 honor level are those for whom the "Honor" column in the "users" table contains the values "Mx" or "Tr", which correspond to Max and Three.

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
