# Instructions
You are working in the `toxicology` database.

Answer the following question:
What is the hallmark bond prevalence rate among molecules from the third batch processed during the preliminary study period that contain trace indicator elements?

## Additional Context
The following clarifications are provided to help you complete this task:

### The term "hallmark bonds" has no standard chemistry definition and could refer to any of the bond classification codes in the database. Without clarification, it is impossible to determine which bond type to filter on.
Interpret "hallmark bonds" as single bonds, identified by the bond_type code '-' in the bond table. A molecule "has hallmark bonds" if it contains at least one bond where bond_type = '-'.

### The phrase "preliminary study period" lacks a specific date range. It could refer to the first year of the study, the first half of the data, or any arbitrary date boundary.
Interpret "preliminary study period" as molecules with dates strictly before 2003-09-01 (exclusive).

### The question asks to filter the data for "Batch 3", but it is unclear what exact string value should be matched. It is ambiguous whether the filter should look for the full phrase, a numeric value, or an alphanumeric abbreviation.
Interpret "Batch 3" as the specific alphanumeric string 'B3'. Filter the data using exactly batch_code = 'B3'.

### The business information defines "bond prevalence metrics" as a "normalized frequency measure against the applicable reference baseline," but does not clarify whether this means a bond-level count ratio, a molecule-level count ratio, a per-molecule averaged proportion, or a ratio against the entire database. The ambiguous phrasing leaves at least four plausible calculation methods.
Calculate the prevalence rate as a molecule-level binary ratio: (count of distinct molecules in the filtered set that have at least one bond of the specified classification) / (count of all distinct molecules in the filtered set) × 100. Use COUNT(DISTINCT molecule_id) for both numerator and denominator — do not count individual bond rows, compute per-molecule averages, or use the entire database as the denominator.

### The database has a `bond` table (with molecule_id and bond_type), a `connected` table (linking atoms to bonds), and an `atom` table (linking atoms to molecules), creating three plausible strategies for determining a molecule's bond classifications. It is unclear whether to join `molecule` → `bond` directly, route through `atom` → `connected` → `bond`, or use `connected` as the central joining table.
Evaluate hallmark bonds strictly locally so, you must route the query through the connected table (atom → connected → bond) to only consider bonds that are directly attached to the filtered trace indicator elements ('p', 'na', 'br', 'sn'). Do not join the bond table directly to the molecule table.

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
