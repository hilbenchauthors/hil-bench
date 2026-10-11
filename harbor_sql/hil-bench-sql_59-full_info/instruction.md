# Instructions
You are working in the `toxicology` database.

Answer the following question:
During the early cataloging phase, how many distinct structural linkages do the 19th-position atoms (those with an atom id that contains _19) in high-risk molecules form with prevalent heteroatoms?

## Additional Context
The following clarifications are provided to help you complete this task:

### "Prevalent heteroatoms" is not a standard classification and could include any non-carbon non-hydrogen elements such as N, O, S, Cl, Br, P, F, Na, or various subsets depending on the analytical context.
Interpret prevalent heteroatoms are nitrogen (n), oxygen (o), and sulfur (s).

### "Early cataloging phase" does not specify a concrete date range, and the registration dates span over a decade, making it impossible to determine which portion of the timeline qualifies.
The early cataloging phase covers molecules with registration_date between January 1, 2010 and December 31, 2011 (inclusive).

### The question references "high-risk molecules", but the business information does not define which risk_level values correspond to the high-risk classification. 
High-risk molecules are those with a value above 60 in the risk_level column in the molecule table. This can be filtered with molecule.risk_level > 60

### The business information describes structural linkages as "primary bonding interactions" without clarifying whether this includes all bond orders or only specific bond types.
Structural linkages include only single bonds, represented by the value '-'.

### The schema contains three tables with overlapping connectivity data: bond, atom_bonds, and connected, each representing atom-to-atom relationships in a different structure, making it unclear which table should be used for atom-level connectivity queries.
Use the connected table, filtering where the target atom appears in the atom_id column, as the primary source for atom-level connectivity queries.

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
