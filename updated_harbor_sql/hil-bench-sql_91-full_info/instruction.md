# Instructions
You are working in the `financial` database.

Answer the following question:
List the account IDs of account holders with active loyalty status in economically distressed districts who made credit card transactions with amounts below the regional threshold, converted to EUR at the current exchange rate.

## Additional Context
The following clarifications are provided to help you complete this task:

### The term "regional threshold" in the question can be interpreted in multiple valid ways. It is unclear whether the threshold refers to a fixed value per region, the average transaction amount per region, the median, a percentile, or some other metric.
The regional threshold refers to the average amount of credit card transactions (operation = 'VYBER KARTOU') in the year 1998 across all regions. Use the overall average, not per-region thresholds.

### The question requires converting transaction amounts to EUR "at the current exchange rate." This is real-time information that changes constantly, does not exist in the database, and cannot be derived from any stored values. The USD/EUR exchange rate must be obtained from an external source at the time of query execution.
Use the current USD to EUR exchange rate of 0.8614 (1 USD = 0.8614 EUR), obtained from Wise.com on January 15, 2026.

### The business information states that "economically distressed districts have performance indicators reflecting challenging market conditions." This definition is confusing because it does not specify which column(s) to use, what numeric threshold defines "distressed" or what comparison method to apply. Terms like "performance indicators" and "challenging market conditions" are vague and do not map to actionable SQL criteria.
Economically distressed districts are those with an unemployment rate greater than 5%.

### The question references "account holders with active loyalty status" but no definition exists in the business information. There is no explanation of what "loyalty status" means, how it is determined, which table or column stores this information, or what criteria qualify an account holder as having "active" status.
"Active loyalty status" refers to account holders who are registered as OWNER in the disposition table (disp.type = 'OWNER'). Filter using disp.type = 'OWNER'.

### The columns A12 and A13 in the district table are described as "District composite score (assessment)" without specifying what metric they represent. A composite score could be any combination of factors (economic health, crime index, development score, unemployment, etc.). Without knowing what these columns measure, it is impossible to use them correctly for filtering "economically distressed" districts.
Column A12 represents the unemployment rate in 1995, and column A13 represents the unemployment rate in 1996. Use A13 (the more recent data) to identify economically distressed districts.

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
