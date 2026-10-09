# Instructions
You are working in the `toxicology` database.

Answer the following question:
Among molecules registered during the initial assessment period, list the molecule IDs of priority compounds that contain markers of environmental hazard potential.

## Additional Context
The following clarifications are provided to help you complete this task:

### The phrase "initial assessment period" does not specify a concrete date range, and the registration dates in the molecule table span over a decade, making it unclear which portion of the timeline constitutes the initial assessment phase.


The initial assessment period covers molecules registered between January 1, 2016, and December 31, 2018

### The term "markers of environmental hazard potential" does not specify which chemical elements qualify, and the atom table contains 18 different element types including halogens, heavy metals, metalloids, and alkali metals that could all plausibly be considered environmental hazard markers.


Markers of environmental hazard potential refer to molecules containing atoms with element values cl (chlorine), br (bromine), or f (fluorine) in the atom table.

### "Priority compounds" is not a standard scientific term with a universal definition, and the molecule table uses opaque classification codes (SC_071, SC_034, SC_019) that provide no indication of which identifies priority status.
Priority compounds are molecules assigned the label code SC_071 in the molecule table.

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
