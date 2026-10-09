# Instructions
You are working in the `codebase_community` database.

Answer the following question:
Among the 5 most active users whose last activity date happened within the last days of the platform's operation, what is the id of the post with the most comments for each user? 

The solution should show each user's id and the id of the post in separate columns, ordering the results by highest activity.

## Additional Context
The following clarifications are provided to help you complete this task:

### The phrase "the last days of the platform's operation" does not specify a concrete start date or how many days this period covers.
Interpret "the last days of the platform's operation" as the period from 2014-08-25  to 2014-09-07 (inclusive).

### The term "active user" is defined vaguely in the business information, the term "actions" is vague and does not specify which platform activities should be counted to determine the most active user.
Treat 'actions' as rows in postHistory with a non-null, positive UserId. The most active users are those with the highest total count of such rows across the entire database (do not restrict this count to the 'last days' date range)

### Comment volume can be interpreted using multiple comment-related metrics available in the schema, and there is no guidance on which metric should be treated as the authoritative count for comparing posts in this question.
The number of comments for a post is determined by the VerifiedCommentCount column from the posts table.

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
