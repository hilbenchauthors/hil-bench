# Instructions
You are working in the `codebase_community` database.

Answer the following question:
List the top 10 verified senior-tier members who have authored the most posts about time series concepts. For each member, report their display name, the number of matching posts, and the total bounty amount in USD awarded on their matching posts, computed as the sum of bounty amounts converted from EUR to USD using today’s EUR/USD exchange rate. Round the USD total to 2 decimal places. Treat “authored posts” as posts created by the user (not edits), and include both questions and answers. Order results by matching post count in descending order, breaking ties by display name in ascending order.

## Additional Context
The following clarifications are provided to help you complete this task:

### The question asks for posts about “time series concepts” but does not specify the exact matching rule to identify them. Multiple related tags could reasonably be used, and different choices change which users rank in the top 10.
Treat “posts about time series concepts” as questions whose tags include any of <time-series>, <forecasting>, <arima>, and answers whose parent question is one of those matching questions. Match using tags only (via the parent question), not title/body text.

### The question requires converting bounty amounts from EUR to USD using today's EUR/USD exchange rate, which is a real-time value not available in the database. A specific exchange rate must be provided for a deterministic USD total.
Use 1 EUR = 1.1806 USD as today’s EUR/USD exchange rate.

### The question references “senior-tier members,” but the business information does not define what qualifies a user for this status. Multiple platform attributes could plausibly be used to determine senior-tier status.
Treat a senior-tier member as a user who has authored at least 100 posts total, counted as COUNT(*) over posts where posts.OwnerUserId = users.Id, with no tag/date/post-type restrictions.

### The schema indicates that certain badge names can reflect trust/verification statuses, but it does not specify which badges.Name value corresponds to a “verified” account. Several trust-related badge names exist, so the correct filter value cannot be inferred from the schema alone.
Treat “verified” users as those who have received the badge where badges.Name = 'Custodian'. Filter users by requiring at least one row in badges with badges.UserId = users.Id and badges.Name = 'Custodian'.

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
