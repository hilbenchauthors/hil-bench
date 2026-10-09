# Instructions
You are working in the `codebase_community` database.

Answer the following question:
Could you provide the account ID of young users with a high notoriety score who are also active users (last accessed more than 15 years ago). Include the number of contributions and their username.

## Additional Context
The following clarifications are provided to help you complete this task:

### The question asks for 'active users' but also specifies 'last accessed more than 15 years ago', which implies inactive users. These two requirements contradict each other.
An active user is one whose LastAccessDate is within 15 days of the most recent LastAccessDate in the users table (inclusive). Compute the reference date as MAX(users.LastAccessDate).

### The concept contributions could be interpreted in more than a valid way, as it could refer to comments, edits, votes, etc.
Contributions are defined as total interactions by summing, for each user, the engagement counts across all posts they own (AnswerCount + CommentCount + FavoriteCount) and adding the user-level vote totals (UpVotes + DownVotes). Posts must be linked using posts.OwnerUserId = users.Id, and missing counts should be treated as 0.

### The term young is not precisely defined and it could vary depending on the user or the context.
Search for users who users.Age is BETWEEN 14 and 25.

### Business information explains that notoriety score is based on reputation and votes, but how to calculate the score based on those values remains unclear.
A High Notoriety score is defined as users.Reputation + (users.UpVotes / users.DownVotes) >= 300 , computed using real-number division. Treat DownVotes that are NULL or 0 as 1 in the denominator (use CASE WHEN DownVotes IS NULL OR DownVotes = 0 THEN 1 ELSE DownVotes END).

### There are several columns in multiple tables referring to some type of user name with unclear or contradictory descriptions.
Use the users.User column as the source for the username.

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
