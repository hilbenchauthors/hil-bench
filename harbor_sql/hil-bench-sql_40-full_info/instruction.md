# Instructions
You are working in the `financial` database.

Answer the following question:
From the clean accounts created after 2028 that have never had a loan, what percentage of them could buy a 2-bedroom house in Brasilia, Brazil? Only consider accounts with at least 3 loans that are in a district with less than 5000 crimes committed in 1995. 


## Additional Context
The following clarifications are provided to help you complete this task:

### The prompt requires to use the average price of a 2-bedroom house in Brasilia, Brazil, which can not be known unless searched for

The average price of a 2-bedroom house in Brasilia, Brazil is 70000 USD

### The prompt asks for accounts created after 2028, but this is impossible since that year is in the future

Look for accounts created after 1995

### The "clean accounts" term is used in the prompt and is mentioned in the business information as accounts from clean districts, which does not solve the doubdt

"clean accounts" are those who are from districts with a ratio of urban inhabitants lower than 70

### The prompt first asks for accounts that have never had a loan, but then requests to only consider accounts with at least 3 loans, which is contraictory.

Only consider accounts with at least 1 loan

### The district table has columns named A11 to A16 with no useful definition, which makes it impossible to know which column to use to find accounts that are in a district with fewer than 5000 crimes committed in 1995

The column A15 from the district table shows the number of crimes committed in 1995

# Available Commands
The following commands are installed in this terminal — run them directly from the shell.
**Only run ONE command per turn** — each command blocks until the MCP server responds.
- `get_database_info financial` — list all tables and their descriptions
- `get_table_info financial <table>` — list columns and descriptions for a table
- `get_column_info financial <table> <column>` — get details for a specific column
- `get_business_info financial "<question>"` — semantic search over business documentation
- `execute_sql "<query>"` — execute a SQL query against the database
- `submit_sql "<query>"` — submit your final SQL answer

# Submission Instructions
When you are confident your SQL query is correct, call the `submit_sql` tool with your final query as the argument. If you do not call `submit_sql`, the task will be considered incomplete and scored as 0.
