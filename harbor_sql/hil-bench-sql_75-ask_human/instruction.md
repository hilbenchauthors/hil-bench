# Instructions
You are working in the `toxicology` database.

Answer the following question:
For each of the elements that are commercially viable to obtain or are usually used in organic compounds, what is their average balanced chemical proportion in our whole dataset? Display the element's chemical name in lowercase (such as "c" for carbon) alongside the average balanced chemical proportion rounded to 4 decimal places, and order the results by average balanced chemical proportion in descending order.

I think the best way to do this is to calculate the average balanced chemical proportion for all elements and then only show the elements that are commercially viable to obtain or are usually used in organic compounds.

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
