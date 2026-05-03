# Instructions
You are working in the `financial` database.

Answer the following question:
List the disposition types of loan-eligible accounts located in western districts (order in descending alphabetical order). Only consider districts where the unemployment rate exceeds 4% and the account has a loan with problematic repayment indicators issued in the recent period.

## Additional Context
The following clarifications are provided to help you complete this task:

### The prompt asks for "western districts", which makes it unclear what to look for since there are districts with "West" in the name and also a "Longitude" column.

The western districts are those with a longitude of over 13.88.

### The phrase "recent period" does not specify a clear date range or reference point, making it unclear which loans should be included in the query.
The recent period refers to loans issued from February 10, 1997, onwards.

### The term "problematic repayment indicators" does not specify which loan status codes (A, B, C, or D) should be considered problematic, as multiple statuses could reasonably fit this description.
Problematic repayment indicators include status codes B (contract finished, loan not paid), C (running contract, OK so far), and D (running contract, client in debt).

### The term "loan-eligible accounts" refers to a bank-specific policy that determines which disposition types can apply for loans, but this eligibility rule is not defined in the business information.
Loan-eligible accounts are those where the disposition type is 'OWNER'.

### The question asks to filter districts where the unemployment rate exceeds 4%, but the unemployment column contains letters, making it unclear how to use it.
The districts where unemployment exceeds 4% are those in which column A13 in the district table has values "A", "F", "J", or "Q".

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
