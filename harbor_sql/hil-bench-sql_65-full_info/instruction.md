# Instructions
You are working in the `card_games` database.

Answer the following question:
I want to do an exhibition of the cards produced by our most successful artists, showing their ability to depict huge monsters. Among all cards that are illustrated by him and have the name of a huge monster, what percentage of them are unique?

## Additional Context
The following clarifications are provided to help you complete this task:

### The prompt asks for cards that have the name of a "huge monster", which makes it unclear which names can be considered as such exactly

The cards that have the name of a "huge monster" are those that contain the words "Dragon", "Colossus", "Cyclops", "Weaver", "Sentry", or "Djinn" in their name. This can be done using: name LIKE "%Dragon%".

### The prompt mentions the "most successful artists", but it is not explained who they are.

Our most successful artists are Amy Weber, Chris Rahn, and Greg Staples. You can look for them using: artist IN ('Amy Weber', 'Chris Rahn', 'Greg Staples')

### The "uniqueness" column in the "cards" table contains values that are not clear yes or no, or even numeric and can not be interpreted. It is impossible to understand how to use this column to determine if a card is unique

Unique cards are those in which the "uniqueness" column in the "cards" table contains values "1", "2", "U", or "P"

# Available Commands
The following commands are installed in this terminal — run them directly from the shell.
**Only run ONE command per turn** — each command blocks until the MCP server responds.
- `get_database_info card_games` — list all tables and their descriptions
- `get_table_info card_games <table>` — list columns and descriptions for a table
- `get_column_info card_games <table> <column>` — get details for a specific column
- `get_business_info card_games "<question>"` — semantic search over business documentation
- `execute_sql "<query>"` — execute a SQL query against the database
- `submit_sql "<query>"` — submit your final SQL answer

# Submission Instructions
When you are confident your SQL query is correct, call the `submit_sql` tool with your final query as the argument. If you do not call `submit_sql`, the task will be considered incomplete and scored as 0.
