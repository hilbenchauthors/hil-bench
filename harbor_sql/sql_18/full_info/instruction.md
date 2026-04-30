# Instructions
You are working in the `financial` database.

Answer the following question:
What is the average loan amount for high-risk clients from urban districts with stable economic conditions?

## Additional Context
The following clarifications are provided to help you complete this task:

### The term "high-risk clients" is not defined and could refer to clients with loan payment issues, clients in economically vulnerable regions, or clients with certain demographic characteristics.
High-risk clients are those whose accounts are located in districts (use account.district_id) where the unemployment rate exceeds 6.0% in either 1995 (A12) or 1996 (A13).

### The business information defines "urban districts" as areas with "high urbanization levels" but does not specify what threshold constitutes "high".
Urban districts are those with urbanization ratio (A10) > 65.

### The district table contains three separate economic metrics (economic_resilience, financial_health_score, and development_index) but it is unclear which metric or combination should be used to determine "stable economic conditions".
Stable economic conditions are calculated as (economic_resilience * 2 + financial_health_score * 3 + development_index) / 6. Districts with a stability score above 50 are considered to have stable economic conditions.

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
