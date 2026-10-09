# Instructions
You are working in the `codebase_community` database.

Answer the following question:
How many users from North American tech hubs with specialized tags and who are eligible for mentorship recognition, earned badges in the first few months of 2011, and are active contributors?

## Additional Context
The following clarifications are provided to help you complete this task:

### It is unclear what time period "the first few months of 2011" refers to.
The first few months of 2011 refers to January and February  2011 only. Filter where Date >= '2011-01-01' AND b.Date < '2011-03-01'

### It's unclear which specific tags are considered "specialized", as there is no definition of which tags qualify as specialized, all special tags, or only select?
Specialized tags refer to posts tagged with: regression, hypothesis-testing, mathematical-statistics, bayesian,  or statistical-significance. Use: p.Tags LIKE '%<regression>%' OR p.Tags LIKE '%<hypothesis-testing>%' OR p.Tags LIKE '%<bayesian>%' OR p.Tags LIKE '%<mathematical-statistics>%' OR p.Tags LIKE '%<statistical-significance>%'

### It is unclear how eligible for mentorship recognition is measured, as the business information is vague as it doesn't mention what the criteria is.
Users eligible for mentorship recognition are those who have earned the Teacher, Enlightened, or Guru badge at any point in their history. Filter using:  SELECT DISTINCT UserId 
    FROM badges 
    WHERE Name IN ('Teacher', 'Enlightened', 'Guru')

### The user_status table contains three columns with coded values, and it is unclear which column and which value should be used to identify "active contributors".
Active contributors are identified using the activity_level column in the user_status table with the value 'Frequent'. Filter using: JOIN user_status us ON u.Id = us.Id WHERE us.activity_level = 'Frequent'

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
