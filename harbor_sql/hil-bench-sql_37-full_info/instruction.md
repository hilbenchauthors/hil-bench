# Instructions
You are working in the `toxicology` database.

Answer the following question:
How many carcinogenic organic hydrocarbon compounds containing reactive metals contain heteroatoms?

## Additional Context
The following clarifications are provided to help you complete this task:

### The question asks for "reactive metals" without specifying which metallic elements should be included. "Reactive metals" could refer to alkali metals (Na, K, Li), alkaline earth metals (Ca, Mg), transition metals, or a broader set of metallic elements. The specific element values in the 'element' column are not clarified.
"Reactive metals" should be interpreted as alkali metals, specifically sodium (Na) and potassium (K), which are the most chemically reactive metallic elements due to their single valence electron. The query should filter for molecules containing either of these elements.

### The term "organic compounds" is not precisely defined in the question. While organic typically refers to carbon-based molecules, it's unclear whether any molecule containing carbon qualifies, or if stricter criteria apply such as requiring carbon-hydrogen bonds, excluding inorganic carbon compounds, or having a minimum carbon atom count.
"Organic compounds" are molecules that contain at least one carbon-hydrogen (C-H) bond. This definition excludes purely inorganic carbon compounds while focusing on the characteristic C-H bonding of organic chemistry.

### The requirements "hydrocarbon compounds," "containing reactive metals," and "contain heteroatoms" are contradictory. By chemical definition, hydrocarbons contain only hydrogen and carbon atoms. Both reactive metals (Na, K) and heteroatoms (O, N, S, Cl) are elements other than H and C. A compound cannot be a hydrocarbon (only H and C) while simultaneously containing reactive metals or other heteroatoms.
Prioritize "hydrocarbon compounds" over "containing reactive metals" and "contain heteroatoms". The query should filter for molecules containing exclusively hydrogen and carbon atoms, with no other elements present. The conditions requiring reactive metals and heteroatoms should be ignored to resolve the contradiction.

### The business information identifies the label column as the source for carcinogenicity, but it is confusing because it does not specify which value indicates a positive carcinogenic result.
A molecule is considered carcinogenic if the label column contains the value '+', which represents a positive test result

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
