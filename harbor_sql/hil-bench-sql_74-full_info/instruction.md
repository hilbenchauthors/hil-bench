# Instructions
You are working in the `toxicology` database.

Answer the following question:
Among priority compounds evaluated after the IUPAC recognition of element 120 (Unbinilium), which chemical element appears in the fewest distinct molecules?

## Additional Context
The following clarifications are provided to help you complete this task:

### The question references "the IUPAC recognition of element 120 (Unbinilium)," but element 120 has never been synthesized or officially recognized by IUPAC.
Element 120 (Unbinilium) has no official IUPAC recognition date and to resolve this, use the year 2011 (the period of notable synthesis attempts at JINR) as the reference point for this event. Treat the phrase "after the IUPAC recognition of element 120" as meaning "year >= 2011".

### The question asks about "priority compounds," but the business information does not define what makes a compound a "priority" compound. The tier_code column has five possible values (T1–T5), and it is unclear which tier code(s) correspond to "priority."
Interpret "priority compounds" as molecules classified under tier_code = 'T2' in the molecule table.

### The question filters molecules "evaluated after" a certain year, but the molecule table has four year columns, initial_screening_year, formal_review_year, classification_year, and publication_year,  with no clear indication of which one represents when a molecule was "evaluated.
Interpret "evaluated after" as referring to the classification_year column in the molecule table.

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
