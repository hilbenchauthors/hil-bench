# Instructions
You are working in the `financial` database.

Answer the following question:
How many premium clients with stable contracts have accounts with superior operational activity but are minors for financial services in urban regions?

## Additional Context
The following clarifications are provided to help you complete this task:

### The question requests "premium clients" who are "minors for financial services," which creates a logical contradiction since premium services require legal age of majority.
For this analysis, consider "premium clients" as those with card type 'gold', and "minors for financial services" as clients born after January 1, 1983.

### The term "superior operational activity" can be interpreted in multiple ways: number of transactions, total balance, account frequency, or a combination of operational factors.
"Superior operational activity" is defined as accounts that have more than 50 transactions recorded in the trans table.

### The business information defines "stable contracts" as those with "good credit performance," but this definition is vague and does not specify which status values qualify as good performance.
Stable contracts are accounts that have at least one loan with loan.status = 'C'.”

### The question asks for "urban regions" but the district table description states it tracks "various district-level socio-economic and demographic metrics distributed across multiple coded attributes," making it unclear whether this table contains the appropriate urbanization classification needed or if the data structure supports identifying urban regions.
The district table does contain urbanization data; use column A10 (ratio of urban inhabitants) with the threshold A10 >= 70 to identify urban regions (at least 70% urban inhabitants).

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
