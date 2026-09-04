# Instructions
You are working in the `financial` database.

Answer the following question:
List the 20 male or female account holders with most significant unpaid loan and include their loan risk ratio. Make sure to include only one loan per client and list only the client ID and the loan risk ratio.

## Additional Context
The following clarifications are provided to help you complete this task:

### The expression “most significant loan" has multiple interpretation it could mean the largest loan, the higher value loan, or even the loan with the higher pay per month.
Identify most significant loan as the loans with the higher loan.payment.

### The expression “account holders" has multiple interpretation it could mean the owner, user, disponent or a combination of these.
Consider account holders of dis.type 'OWNER' or 'DISPONENT'.

### The task does not provide business information indicating what does loan risk ratio means.
To compute the risk ratio filter by loan.status 'B' and 'D' and divide the loan.amount by the distric.A11 (average salary).

### The gender column uses non-semantic coded values that do not clearly indicate the gender they represent. The column has values for A,B,C and D and is not clear which values is for Males and which one is for female.
Use the gender.value 'A' to filter for female clients and the gender.value 'B' to filter for male clients.

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
