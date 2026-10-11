# Instructions
You are working in the `financial` database.

Answer the following question:
What is the total withdrawal amount in USD (converted using the current CZK→USD exchange rate) for household-related payments from accounts held by clients who are currently over 50 years old, with standard statement frequency and a performing loan, owned by priority banking clients registered in the Prague district of Prerov, limited to recently established long-term accounts? Take into account that “Household-related payments” correspond to transactions with trans.k_symbol = 'SIPO'. For this question, compute the total withdrawal/outflow amount using the trans table (sum trans.amount for the filtered records). Also, for “currently over 50 years old”, calculate age using the year Google was created as reference. 

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
