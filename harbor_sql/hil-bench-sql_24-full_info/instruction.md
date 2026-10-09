# Instructions
You are working in the `codebase_community` database.

Answer the following question:
Among posts that discuss clustering topics during the last few months, which one has better acceptance and is eligible for success? Show only the title.

## Additional Context
The following clarifications are provided to help you complete this task:

### The question asks for posts with "better acceptance," which is a vague term that can be interpreted as higher view count, higher score, more favorites, or having an accepted answer.
The posts with "better acceptance" are the ones with a higher view count.

### The question refers to "the last few months" without specifying which calendar period this corresponds to.
The last few months refer to the period between 2014-04-01 and 2014-08-31 (inclusive).

### The question asks to filter posts that are about "clustering," but the keywords used to match that concept are undefined.
Posts that discuss "clustering" are those containing the keyword "clustering", "cluster analysis", "unsupervised learning", or "grouping" in their body.

### The business information defines "eligible for success" as posts with "low correspondence," but the meaning of "low correspondence" remains unclear and could map to many different columns or conditions.
Low correspondence = 0 links in postLinks where the post appears as PostId or RelatedPostId (any LinkTypeId).

### The question asks to filter only posts from the last few months, but it is unclear which column should be used to determine the date of each post. 
Use the "CreatedDate" column in the posts table to filter posts by date.

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
