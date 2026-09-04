# Instructions
You are working in the `financial` database.

Answer the following question:
List the number of priority-tier clients with indexed accounts who have fully repaid active loans with a duration exceeding 100 months, residing in districts whose economic distress indicator corresponds to the 5th-highest value.

## Additional Context
The following clarifications are provided to help you complete this task:

### The question asks for loans with a duration exceeding 100 months, but the loan table only contains durations up to 60 months, making this requirement impossible to satisfy.
Use loans with a duration of 48 months.

### The phrase "fully repaid active loans" contains contradicting requirements, as a loan cannot be both fully repaid and active simultaneously.
Filter for loans with status 'C' which would signify loan repaid.

### The term "priority-tier clients" can be interpreted as clients based on age, account balance, transaction volume, loan history, or card type, making the filtering criteria unclear.
Priority-tier clients are those born before January 1, 1950.

### The term "indexed accounts" is not defined in the business information or database descriptions, making it unclear what criteria determine indexed status for accounts.
Indexed accounts are those with a monthly statement frequency (frequency = 'POPLATEK MESICNE').

### The question refers to an “economic distress indicator”, but the district table contains multiple numeric economic metrics (A11, A12, A13, A17) that are not directly comparable or rankable against each other, as they are compiled using different measurement bases, scales, and reference populations. Without knowing which metric is intended, applying a ranking across districts is ambiguous because ranking by different columns produces different and incompatible district orders.
Use column A17 (labor compilation) for the economic distress indicator. Rank all districts by A17 in descending order and select the A17 value of the 5th row (using ORDER BY A17 DESC LIMIT 1 OFFSET 4, without DISTINCT).

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
