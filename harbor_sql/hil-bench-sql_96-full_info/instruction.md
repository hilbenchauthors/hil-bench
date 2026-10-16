# Instructions
You are working in the `card_games` database.

Answer the following question:
What are all the cards with names that reference a forest animal and have a normal layout, original release date of 1991, black border color, availability in mtgo or paper, life that is less than 0, and are very powerful? Only consider cards with life values above 4 and provide only their name. Order the results in alphabetical descending order.

## Additional Context
The following clarifications are provided to help you complete this task:

### Question asks for a filter of cards in a release date in which the card game was not invented yet (Magic was released by Wizards of the Coast in 1993).
Consider cards with a null original release date

### The question expects cards with life values being higher than 4 while also being lesser than zero.
Only consider cards with null life.

### The prompt asks for cards whose names reference a forest animal, but the exact values for which to filter for are not clear.

To look for cards whose names reference a forest animal, look for names containing the exact words "wolf", "rat", "spider", "bear", or "beetle". Nothing more, and do not look for plural names.

### The prompt mentions cards that are "very powerful", but it is not explained what values can be considered as "very".

The "very powerful" cards are those with a power greater than 5.

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
