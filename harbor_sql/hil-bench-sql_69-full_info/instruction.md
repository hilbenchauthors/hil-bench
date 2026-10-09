# Instructions
You are working in the `codebase_community` database.

Answer the following question:
Among elderly adult users younger than 35 who joined after January 2012, who are the top 5 most controversial users based on their Controversy Coefficient? For each user, show their display name and total bounty value from Bounty Start transactions, converted from EUR to USD. In case of ties in Controversy Coefficient, rank by earliest account creation date.

## Additional Context
The following clarifications are provided to help you complete this task:

### The question contains contradictory requirements regarding user age. It asks for "elderly adult users" (which typically refers to significantly older individuals) but then specifies "younger than 35" (which refers to young adults). 
"Elderly adult users" in the community context refers to users who are legally adults (21 years or older) but still in the younger demographic. Therefore, filter for users aged between 21 and 35 (exclusive). Filter using: WHERE u.Age >= 21 AND u.Age < 35

### The request requires converting EURO to USD which is not in the static database.
Use a fixed exchange rate of 1.18 USD per 1 EUR for the conversion calculation.

### The task requires ranking users by a "Controversy Coefficient" but no formula or definition for this metric exists in the business information or database schema.
Calculate the Controversy Coefficient using the formula: (DownVotes * 100.0) / (UpVotes + 1.0).

### The votes table uses a VoteTypeId column with integer codes, but the schema does not define which code corresponds to a "Bounty Start" transaction.
A "Bounty Start" transaction is represented by VoteTypeId = 2.

# Available Commands
The following commands are installed in this terminal — run them directly from the shell.
**Only run ONE command per turn** — each command blocks until the MCP server responds.
- `get_database_info codebase_community` — list all tables and their descriptions
- `get_table_info codebase_community <table>` — list columns and descriptions for a table
- `get_column_info codebase_community <table> <column>` — get details for a specific column
- `get_business_info codebase_community "<question>"` — semantic search over business documentation
- `execute_sql "<query>"` — execute a SQL query against the database
- `submit_sql "<query>"` — submit your final SQL answer

# Submission Instructions
When you are confident your SQL query is correct, call the `submit_sql` tool with your final query as the argument. If you do not call `submit_sql`, the task will be considered incomplete and scored as 0.
