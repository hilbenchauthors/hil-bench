# Instructions
You are working in the `toxicology` database.

Answer the following question:
Among carcinogenic molecules that meet the single-bond-only classification and are structurally complex, what assessment prevalence rate of those molecules also contain diverse bond types? Report the assessment prevalence rate rounded to three decimal places.

## Additional Context
The following clarifications are provided to help you complete this task:

### The question asks for molecules with "single-bond-only classification" that also "contain diverse bond types," which presents logically contradictory requirements since single-bond-only status and diverse bond types appear mutually exclusive.
Treat "single-bond-only classification" as single_ratio >= 0.80 (single bonds / total bonds) per molecule, and treat "diverse bond types" as COUNT(DISTINCT bond_type) >= 2 per molecule; interpret “also contain diverse bond types” as applying the diversity condition on top of the single-bond-only base set.

### "Structurally complex molecules" can be interpreted as molecules with a high total atom count, molecules with many distinct element types, molecules with a high bond-to-atom ratio, or molecules with a large number of non-hydrogen atoms.
"Structurally complex molecules" refers to molecules with more than 20 atoms. Filter using: COUNT(atoms) > 20 per molecule.

### The business information lists multiple assessment prevalence rate methodologies (simple molecule-count ratio, atom-weighted incidence proportion, bond-frequency normalization factor, and structure-adjusted rate) without specifying which methodology applies to this analysis.
Use the bond-frequency normalization factor by weighting molecules by their total bond count, where total_bonds is computed as COUNT(DISTINCT bond_id) from the bond table per molecule_id: compute 100 * SUM(total_bonds) over the target subset divided by SUM(total_bonds) over the reference set, rounded to three decimals.

### The molecule table's label column uses screening assessment codes (e.g., C7, M2, Q9, D4, K8, W1), but the schema does not document which codes correspond to carcinogenic outcomes, making it unclear how to filter carcinogenic molecules.
Treat carcinogenic molecules as those with label IN ('C7','M2','Q9').

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
