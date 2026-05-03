# Instructions
You are working in the `card_games` database.

Answer the following question:
What are all the cards with names that reference a forest animal and have a normal layout, original release date of 1991, black border color, availability in mtgo or paper, life that is less than 0, and are very powerful? Only consider cards with life values above 4 and provide only their name. Order the results in alphabetical descending order.

# Available Commands
The following commands are installed in this terminal — run them directly from the shell.
**Only run ONE command per turn** — each command blocks until the MCP server responds.
- `get_database_info card_games` — list all tables and their descriptions
- `get_table_info card_games <table>` — list columns and descriptions for a table
- `get_column_info card_games <table> <column>` — get details for a specific column
- `get_business_info card_games "<question>"` — semantic search over business documentation
- `execute_sql "<query>"` — execute a SQL query against the database
- `ask_human "<question>"` — ask a specific clarifying question about a task blocker
- `submit_sql "<query>"` — submit your final SQL answer

# Submission Instructions
When you are confident your SQL query is correct, call the `submit_sql` tool with your final query as the argument. If you do not call `submit_sql`, the task will be considered incomplete and scored as 0.
