# Instructions
You are working in the `toxicology` database.

Answer the following question:
What is the percentage of double-bond records among all eligible bond records in phosphorus compounds, excluding bonds formed through ionic interactions, considering only molecules that are water-free hydrates and have a significant molecular structure? Provide the result as a single percentage value rounded to 4 decimal places.

## Additional Context
The following clarifications are provided to help you complete this task:

### The question asks to exclude "bonds formed through ionic interactions," but all bonds in molecular structures are covalent. Ionic bonds form lattice structures, not discrete molecular bonds, so no bonds in the database are ionic.
Reinterpret "ionic interactions" as highly polar bonds, this is, those involving hydrogen, which forms the most polar covalent bonds in organic compounds. Exclude all bonds where either endpoint atom is hydrogen (element <> 'h').

### The question contains contradictory requirements regarding molecule classification. It asks for "water-free hydrates," where "water-free" (anhydrous) means lacking water molecules while "hydrate" specifically refers to compounds containing water.
Treat "water-free hydrate" as a molecule containing at least one oxygen atom but no O-H bonds.

### The phrase “significant molecular structure” supports multiple distinct interpretations, such as measuring size by total atom count, by non-hydrogen atom count, or by bond count.
Define "significant molecular structure" as a molecule having at least 20 bonds in the bond table.

### The business info states double-bond records are reportable only when "chemically active within a molecule's oxygen participation," but the criteria are unclear.
A double bond is reportable when bond_type = '=' and one endpoint has element = 'c' while the other has element = 'o'.

### The business information states that phosphorus must "play a meaningful structural role" for a compound to qualify as a phosphorus compound, but this criterion is vague and lacks specific chemical or database-measurable criteria.
A molecule qualifies when it contains at least one atom with element = 'p' and the molecule has label = '-' in the molecule table.

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
