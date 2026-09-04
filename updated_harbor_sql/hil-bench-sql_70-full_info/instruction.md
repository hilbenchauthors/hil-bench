# Instructions
You are working in the `financial` database.

Answer the following question:
List the districts where the bank's target segment of customers are associated with accounts opened in the first days of February 1997, regardless of their account role.

## Additional Context
The following clarifications are provided to help you complete this task:

### The question asks for accounts opened in "the first days of February 1997" but does not specify how many days constitute "the first days." It is unclear whether this means the first 10 days, first 15 days, first week, or some other timeframe.
"The first days of February 1997" means February 1 and February 2, 1997 only.

### The business information defines "the bank's target segment of customers" as "clients from demographics with higher growth potential," but this definition is vague and does not specify which demographic attribute or criteria determines growth potential. It is unclear whether this refers to age, income level, gender, location, or some other factor.
The bank's target segment of customers refers to female clients only (gender = 'F'). Filter for clients where gender = 'F' when identifying the target segment.

### The account table structure includes three date-related columns (requested_date, bank_approved_date, customer_approved_date) tracking different lifecycle stages, but the table description does not clearly explain the relationship between these dates or which stage represents the official account opening. The table's multi-stage date architecture is confusing and makes it unclear how to interpret the account timeline.
The account table tracks a multi-stage process: requested_date represents when the account opening was initiated, bank_approved_date represents internal approval, and customer_approved_date represents final confirmation. For determining when accounts were "opened," use requested_date as this is the official account opening date.

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
