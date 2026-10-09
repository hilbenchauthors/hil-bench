# Instructions
You are working in the `codebase_community` database.

Answer the following question:
What is the average activity percentage of members with good badges who authored lengthy posts that were among the most popular posts during the first few years of the platform? Return the authors and the average activity percentage.

## Additional Context
The following clarifications are provided to help you complete this task:

### The question asks for "most popular posts", but popularity can be measured in multiple ways, such as highest score, highest view count, highest comment count.
A post is considered popular if it has a FavoriteCount of 2 or more.

### The term "lengthy post" is not precisely defined. It is unclear what character or word count qualifies a post as lengthy.
A lengthy post is defined as one where the character count of the body exceeds 2,500 characters.

### The phrase "first few years of the platform" is ambiguous, it could mean the first year only, the first two years, or the first three years or more. 
The first few years of the platform refers strictly to posts with CreaionDate >= '2009-01-01' AND CreaionDate < '2011-01-01'

### The business information defines "good badges" as those considered to be relevant to the platform's content and community standards, but the definition is vague and could map to many badges.
Good badges are specifically those awarded for 'Custodian', 'Citizen Patrol', and 'Organizer', badges that recognize users who have maintained content quality on the platform.

### The user_activity_stats table contains three columns that could all plausibly represent a user's activity percentage, with no clear indication of which one represents the activity percentage.
The activity percentage must be taken from the reply_level column in the user_activity_stats table.

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
