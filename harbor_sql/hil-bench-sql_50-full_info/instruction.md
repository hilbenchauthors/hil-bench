# Instructions
You are working in the `toxicology` database.

Answer the following question:
Provide the molecule_id of all molecules that belong to the primary toxicity class, fall within the structural complexity tier, exhibit a significant halogen activity profile, and contain a phosphorus–sulfur linkage based on the dataset’s bond linkage records.

## Additional Context
The following clarifications are provided to help you complete this task:

### The question references “structural complexity tier” but does not define what structural feature, metric, or threshold determines membership in the tier. No schema column or business info provides an operational definition.
Interpret “structural complexity tier” as molecules whose hetero-atom fraction is strictly greater than the dataset-wide average hetero-atom fraction: compute per-molecule hetero_fraction using the atom table (excluding NULL molecule_id and requiring total atoms > 0) as hetero_fraction = COUNT(DISTINCT atom_id where element NOT IN ('c','h')) / COUNT(DISTINCT atom_id). Compute the dataset-wide average as AVG(hetero_fraction) across all molecules in scope, and include molecules where hetero_fraction > avg_hetero_fraction.

### The question uses “primary toxicity class” but provides no definition of what “primary” means and no business info defines how to identify this class from available data.
Interpret “primary toxicity class” as the molecule.label value that appears most frequently in the molecule table (COUNT(*) grouped by label, excluding NULL labels), ordering by count DESC and label ASC, selecting LIMIT 1. A molecule belongs to the primary toxicity class if molecule.label equals that selected label.

### The business information describes “halogen activity” qualitatively (halogen-like elements, reporting standards) and states that a “significant” profile is a “notable structural feature,” but it does not specify which element codes qualify or what quantitative threshold makes the profile significant.
Interpret halogen-like elements as atom.element IN ('f','cl','br','i','s','p'): for each molecule, compute halogen_fraction using the atom table (excluding NULL molecule_id and requiring total atoms > 0) as halogen_fraction = COUNT(DISTINCT atom_id where element is halogen-like) / COUNT(DISTINCT atom_id). Define “significant halogen activity profile” as molecules whose halogen_fraction is strictly greater than the dataset-wide average halogen_fraction, where the average is computed as AVG(halogen_fraction) across all molecules in scope.

### The question requires a phosphorus–sulfur linkage “based on the dataset’s bond linkage records,” but the schema provides multiple plausible representations of linkages (e.g., connected vs bond_record vs bond-level tables), with differing granularity and duplication behavior, and the question does not specify which source defines linkage.
Interpret “bond linkage records” as rows from the connected table restricted to direction_flag = 1 (the primary representation); a molecule satisfies the phosphorus–sulfur linkage condition if there exists at least one connected row (direction_flag = 1) whose endpoints are a phosphorus atom and a sulfur atom (either direction), both belonging to the same molecule_id, and the total number of such qualifying linkage records for that molecule is between 1 and 2 inclusive (COUNT(*) BETWEEN 1 AND 2). This linkage test must be evaluated using connected (direction_flag=1) and atom only.

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
