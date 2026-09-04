# Instructions
You are working in the `toxicology` database.

Answer the following question:
Among molecules that are described as halogenated and qualify as high-load atomic compounds, what percentage exhibit an elevated biohazard score? Round to two decimal places.

## Additional Context
The following clarifications are provided to help you complete this task:

### The prompt asks for "molecules that are described as halogenated", which makes it unclear which exact descriptions can be considered as such. 

The molecules that are described as halogenated are those with the values: 'Halogenated', 'Halogen-bearing',  or 'Chlorinated' in the "description" column of the "molecule" table

### The question asks for what qualifies as "high-load atomic compounds", but this term is not defined anywhere in the business information or schema, making it unclear what threshold this refers to.
High-load atomic compounds are molecules with more than 28 atoms in the atom table. Use: (SELECT molecule_id, COUNT(atom_id) AS atom_count FROM atom GROUP BY molecule_id) a
AND a.atom_count > 28

### The biohazard_score column in the molecule table lacks a definition in the schema for what its numerical values represent or how they should be interpreted. Without knowing the scale or boundaries defined for this column, it is unclear which values qualify as 'elevated'.
An elevated biohazard score refers to molecules with a biohazard_score greater than 62.

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
