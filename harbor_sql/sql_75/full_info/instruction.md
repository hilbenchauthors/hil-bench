# Instructions
You are working in the `toxicology` database.

Answer the following question:
For each of the elements that are commercially viable to obtain or are usually used in organic compounds, what is their average balanced chemical proportion in our whole dataset? Display the element's chemical name in lowercase (such as "c" for carbon) alongside the average balanced chemical proportion rounded to 4 decimal places, and order the results by average balanced chemical proportion in descending order.

I think the best way to do this is to calculate the average balanced chemical proportion for all elements and then only show the elements that are commercially viable to obtain or are usually used in organic compounds.

## Additional Context
The following clarifications are provided to help you complete this task:

### The prompt asks for "elements that are usually used in organic compounds", which makes it unclear which elements it refers to exactly

The elements that are usually used in organic compounds are c, h, o, p, cl, f, ca, and I.

### The prompt mentions "elements that are commercially viable to obtain", but it is not explained which elements this refers to, there is no way to know it.

The elements that are commercially viable to obtain are cu, pb, sn, and na. Using any other element would produce an incorrect result.

### The "balanced chemical proportion" term is used in the prompt and is mentioned in the business information, but the correction factor is not clear.

The correction factor in the balanced chemical proportion is 2 for C, 3 for O and Pb, and 1 for all other elements. For example, the balanced chemical proportion for C in the molecule C2OFH is (carbon_in_molecule/total_number_of_atoms)*correction_factor = (2/5)*2 = 4/5. Note that if the molecule did not contain C, the result would have been 0.

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
