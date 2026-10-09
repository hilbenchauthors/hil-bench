# Instructions
You are working in the `toxicology` database.

Answer the following question:
Which molecules contain a high rate of elements usually found in inorganic compounds vs elements usually found in organic compounds (number_of_inorganic_atoms / number_of_organic_atoms)? List their ID in descending order and add a "Yes" or "No" column that shows whether or not they are safe (use the tox_grade column).


## Additional Context
The following clarifications are provided to help you complete this task:

### The prompt asks for "elements usually found in inorganic compounds", and "elements usually found in organic compounds", which makes it unclear which elements can be considered as such 

The elements usually found in inorganic compounds are: na, sn, pb, zn, cl, br and i, and the elements usually found in inorganic compounds are: c, h, o, n, s, p, and f

### The prompt mentions a "high rate", but it is not explained what is considered as high exactly, regardless of which elements are organic or inorganic. It is missing information from the business information.

A "high rate" of elements usually found in inorganic compounds vs elements usually found in organic compounds is a rate higher than 0.6.

### The "tox_grade" column in the "molecule" table contains values that are numeric and cannot be interpreted as whether a molecule is safe or not. It is impossible to understand how to determine if a molecule is safe or not.

A molecule is safe if the "tox_grade" column in the "molecule" table has the values "L1", "L2", or "L3"

# Available Commands
The following commands are installed in this terminal — run them directly from the shell.
**Only run ONE command per turn** — each command blocks until the MCP server responds.
- `get_database_info toxicology` — list all tables and their descriptions
- `get_table_info toxicology <table>` — list columns and descriptions for a table
- `get_column_info toxicology <table> <column>` — get details for a specific column
- `get_business_info toxicology "<question>"` — semantic search over business documentation
- `execute_sql "<query>"` — execute a SQL query against the database
- `submit_sql "<query>"` — submit your final SQL answer

# Submission Instructions
When you are confident your SQL query is correct, call the `submit_sql` tool with your final query as the argument. If you do not call `submit_sql`, the task will be considered incomplete and scored as 0.
