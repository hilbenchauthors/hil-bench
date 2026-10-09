# Instructions
You are working in the `codebase_community` database.

Answer the following question:
Who are the top 5 active contributors among adult teenagers, ranked by their most popular contributions, considering only those dated after R version 5.0 was released? Show their display name and popularity metric.

## Additional Context
The following clarifications are provided to help you complete this task:

### The question references "R version 5.0 was released," but R version 5.0 has never been released.
Filter for contributions on or after the fixed date 2012-07-01 (inclusive).

### The question asks for "adult teenagers," but the database schema defines "teenager" as users aged 13–18 and "adult" as users aged 19–65. These are mutually exclusive age categories.
Interpret "adult teenagers" as users in the transitional age range of 18 to 21 years old (inclusive), bridging the boundary between the teenager (13–18) and adult (19–65) categories.

### The term "most popular contributions" lacks a specific metric definition and could plausibly mean highest Score, ViewCount, FavoriteCount, CommentCount, or AnswerCount — each producing different rankings.
Interpret "most popular contributions" as the highest total view count from their posts. Rank users by the sum of the ViewCount column in the posts table across all their qualifying posts, from highest to lowest. The output column should display this total. Break ties alphabetically by display name.

### The business information defines "active contributors" as "users who demonstrate strong community participation and consistent engagement," but "strong" and "consistent" are not quantified with any numeric thresholds.
Interpret "active contributor" as a user who has authored at least 5 posts as owner across all time, and has been awarded at least 5 badges in total. Both conditions must be met.

### The question filters posts "dated after" a certain date, but the `posts` table has four date columns:  `CreaionDate`, `LasActivityDate`, `LastEditDate`, and `LastUpdateDate`  with no schema clarification on which represents the relevant "date" of a post.
Interpret "dated after" as the `LasActivityDate` column in the `posts` table.

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
