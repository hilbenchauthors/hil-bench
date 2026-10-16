# Instructions
You are working in the `financial` database.

Answer the following question:
What are the names of the districts where senior account owners whose loans were settled without issues made loan servicing transactions during the crisis period, considering only economically distressed districts?

## Additional Context
The following clarifications are provided to help you complete this task:

### The question refers to "senior account owners" without providing any definition or criteria for determining which clients qualify as senior, making it unclear how to identify the relevant group.
Senior account owners are defined as clients with a birth date earlier than January 1, 1950.

### The term "crisis period" is used without specifying any concrete start or end dates, making it unclear which time range should be applied to transaction activity.
The crisis period is defined as the calendar year from January 1, 1996, to December 31, 1996.

### Transaction records store internal classification codes that group financial activities by accounting purpose, but the data does not specify whether loan servicing corresponds to a single classification code or to multiple related categories, making it unclear which transactions qualify
Loan servicing transactions are defined as transactions where
trans.k_symbol = 'CAT7' AND trans.service_flag = 'S1'.

### The question refers to "economically distressed districts", but the business information does not provide any definition, metric, or threshold for determining economic distress, making it impossible to identify which districts qualify.
Economically distressed districts are defined as districts with an unemployment rate in 1995 greater than 5.0 percent, using the district.A12 column.

### Loan records include an internal classification code assigned during portfolio review, but the schema does not indicate whether the codes represent outcomes, stages, or review categories, nor whether any single code uniquely represents loans settled without issues.
Loans settled without issues are identified by loans where
loan.status = 'R3' AND loan.outcome_group = 'G2'.

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
