# Instructions
You are working in the `codebase_community` database.

Answer the following question:
Provide the Body of posts created by adult teenagers whose account is eligible for the new badge. Consider only posts from users who created their accounts in the month of the 2013 European Girls' Olympiad in Informatics or earlier, and include only posts that are unresolved.

## Additional Context
The following clarifications are provided to help you complete this task:

### The question refers to the 2013 European Girls' Olympiad in Informatics, but the competition was founded in 2021, therefore the request contradicts real world information.
Interpret "2013 European Girls' Olympiad" as 2023 European Girls' Olympiad, which was held in July 2023.

### The question asks for posts by "adult teenagers," but these are contradictory age categories since teenagers are defined as ages 13–18 and adults as ages 19–65, with no overlapping range.
"Adult teenagers" refers to users whose age is between 17 and 19, inclusive.

### The business information states that eligible accounts hold a "high-tier intellectual badge," but this phrase is vague and does not specify which badge names qualify.
High-tier intellectual badges are 'Analytical', 'Socratic', and 'Enlightened'.

### Multiple tables contain status-related columns (postHistory.State, postHistory.PostResolution, posts.ClosedDate) with no guidance on which one determines whether a post is unresolved.
Unresolved posts are those where the State column in the postHistory table equals 'Pending'.

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
