# Instructions
You are working in the `toxicology` database.

Answer the following question:
Provide the molecule_id of all molecules that contain any of the top 5 toxic elements in the latest U.S. EPA TRI report, are classified as halogen-only hydrocarbons, fall within the advanced structural complexity tier, and are classified as high hazard

## Additional Context
The following clarifications are provided to help you complete this task:

### The question asks for molecules that contain any of the top 5 toxic elements in "the latest U.S. EPA TRI report", which requires real-time information. The business info only explains that the raw data from TRI has been processed separately, but doesn't include any information about the processing result. 
The top 5 toxic elements in the latest U.S. EPA TRI report are: lead (pb), nitrogen (n), chlorine (cl), fluorine (f), sulfur (s).

### The request describes molecules as "halogen-only hydrocarbons"; in chemistry, hydrocarbons are compounds composed exclusively of carbon and hydrogen atoms. A classification that is simultaneously "halogen-only" and a "hydrocarbon" is chemically impossible in real-world terminology, making the term inherently contradictory.
Interpret "halogen-only hydrocarbons" as molecules that contain hydrogens (h), carbons (c), one or more halogen atoms (f, cl, br, i), and no other type of element in their recorded atomic composition.

### The phrase “advanced structural complexity tier” references a tiering scheme and complexity definition that are not provided by the dataset schema or contents, leaving the scoring method and cutoff unspecified.
Define complexity_score = 2*n_double + 6*n_triple, where n_double is the count of bonds with bond_type='=' and n_triple is the count of bonds with bond_type='#' for the molecule. Define “advanced structural complexity tier” as molecules whose complexity_score is strictly greater than the dataset median of complexity_score, with ranking ordered by complexity_score ASC and tie-break by molecule_id ASC.

### The question asks to filter elements classified as "high hazard". There is a hazard_index column in the molecule table, but it is unclear whether the numeric scale is ordered by severity, how to interpret its magnitude, or what threshold corresponds to “high.”
Interpret “high hazard” as molecules whose hazard_index falls in the dataset’s upper quartile: compute Q3 by ordering hazard_index ASC with tie-break by molecule_id ASC and selecting the row at position ((3*total + 3)/4), then include molecules with hazard_index >= Q3.

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
