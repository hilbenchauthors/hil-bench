# Instructions
You are working in the `financial` database.

Answer the following question:
What is the total withdrawal amount in USD (converted using the current CZK→USD exchange rate) for household-related payments from accounts held by clients who are currently over 50 years old, with standard statement frequency and a performing loan, owned by priority banking clients registered in the Prague district of Prerov, limited to recently established long-term accounts? Take into account that “Household-related payments” correspond to transactions with trans.k_symbol = 'SIPO'. For this question, compute the total withdrawal/outflow amount using the trans table (sum trans.amount for the filtered records). Also, for “currently over 50 years old”, calculate age using the year Google was created as reference. 

## Additional Context
The following clarifications are provided to help you complete this task:

### The question asks for the total withdrawal amount in USD using the current CZK→USD exchange rate. The database stores amounts in CZK and contains no live FX rates, so the “current” conversion cannot be derived from the DB.
Use CZK→USD = 0.052416 for conversion (USD = CZK × 0.052416).

### The question asks for accounts "registered in the Prague district of Prerov", but Prague and Prerov are independent districts, so this is a real world contradiction.
Interpret this as Prague and Prerov as independent districts. Filter for clients whose district is Prague and Prerov: district.A2 = 'Hl.m. Praha' and 'Prerov' (joined via client.district_id).

### The question asks for "recently established long-term accounts," which contain contradictory requirements. An account cannot simultaneously be recently established (implying new) and long-term (implying old or mature).
Recently established: account.date >= '1997-07-01' (last ~18 months of the dataset ending 1998-12-31). Long-term: the account has an activity span ≥ 365 days, i.e. MAX(trans.date) - MIN(trans.date) >= 365 for that account.

### The question asks for accounts "owned by priority banking clients", but the term "priority banking clients" is not defined in the business information provided, but there is no column in the database explicitly identifying priority status.
Priority banking clients are defined as account owners (disposition type = 'OWNER') who hold a gold-class credit card (card type = 'gold').

### The question filters for accounts “with a performing loan,” but the only relevant field is loan.status, whose values are encoded (e.g., A/B/C/D). If the schema only says “repayment status” and does not define what each code means, it becomes unclear which specific value(s) correspond to a “performing” loan.
Treat a “performing loan” as loans where loan.status = 'B'.

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
