# Instructions
You are working in the `financial` database.

Answer the following question:
What is the average loan amount from loans associated with accounts having a transaction-based reporting cycle during the consolidation period? Only consider loans with a priority status and accounts from a Western district.

## Additional Context
The following clarifications are provided to help you complete this task:

### The term consolidation period defines the time window for the query but is not tied to specific dates.
The consolidation period corresponds to the calendar year 1997.

### The prompt requires filtering for western districts, implying a condition based on the Longitude column (e.g., Longitude < X). However, the specific numerical value (X) needed to define this cutoff is not provided, making it unclear which exact values to include.
Western districts are those with a longitude of over 12.9

### The business info states Transaction-based reporting cycle corresponds to specific account types, which is vague. It doesn't specify the value needed to filter the account records.
The value "POPLATEK MESICNE" in the frequency column of the account table identifies accounts with a transaction-based reporting cycle.

### The question asks for priority loans, but it is not specified which loan statuses qualify as Priority. This should be within the business information but is not defined.
Priority Loans are loans with a status of C (Running OK).

### The loans table has different columns for loan amounts from more than 2 different providers, which makes it impossible to know how to obtain a loan's amount

The loan's amount is given by the apprvd_amount_provider_T column from the loans table

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
