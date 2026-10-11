# Instructions
You are working in the `codebase_community` database.

Answer the following question:
What is the percentage difference in the number of highly engaged users in good standing between 2010 and 2011, calculated according to community guidelines?

## Additional Context
The following clarifications are provided to help you complete this task:

### The term “highly engaged users” is not defined and can reasonably refer to different measurable engagement metrics such as reputation, contribution volume, or post performance.
Highly engaged users are defined as users whose total post score within a given year exceeds 1200.

### The phrase “percentage difference according to community guidelines” is used without specifying the calculation method or normalization approach in the business information.
Percentage difference equals the 2010 proportion of qualifying users minus the 2011 proportion, where each proportion is calculated as qualifying users divided by active users in that year, multiplied by 100.

### The question requires filtering for users in "good standing" without defining the specific thresholds required to satisfy these business criteria
Users in "good standing" are those with a Reputation score of 15 or higher.

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
