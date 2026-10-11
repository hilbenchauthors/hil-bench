# Instructions
You are working in the `financial` database.

Answer the following question:
For accounts with a dependable track record in districts with a high assessment tier, what is the average transaction balance in EUR for each? Provide the account ID and average balance in EUR.

## Additional Context
The following clarifications are provided to help you complete this task:

### The question asks for balances in EUR, but the database stores all monetary amounts in USD. Converting to EUR requires a current USD-to-EUR exchange rate, which is real-time information not available in the database.
The current USD to EUR exchange rate is 0.78. Multiply USD amounts by 0.78 to convert to EUR.

### The business information defines "dependable track record" using vague qualitative language ("prudent financial management," "adequate reserves") that cannot be directly translated into precise SQL filters.
An account has a dependable track record if: (1) the average balance across all its transactions exceeds 50,000 USD, AND (2) the account has more than 250 total transactions. Both conditions must be met.

### The district table has columns A2 through A16 with opaque names and no descriptive metadata, making it impossible to determine which column represents the district's assessment tier or what threshold qualifies as "high."

The district assessment tier corresponds to column A9 in the district table. A district has a high assessment tier when its A9 value exceeds 6. Join the district table to the account table using account.district_id = district.district_id.

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
