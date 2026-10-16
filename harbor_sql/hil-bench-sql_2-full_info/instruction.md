# Instructions
You are working in the `card_games` database.

Answer the following question:
I want to know what is the average balanced power of cards with natural names and for the most played MTG monster currently. Only consider foiled cards and show both values separately so I can compare them. Please ensure that the first column is for elemental names and the second is for MTG monsters.


## Additional Context
The following clarifications are provided to help you complete this task:

### The prompt asks for cards with natural names, but it is unclear what exact search terms should be used to accomplish this.

The cards with natural names are those that contain the "element" word. Strictly name LIKE "%element%".

### The prompt requires comparing with the most played MTG monster. This information is not present in the dataset and needs to be found online.

The most played MTG monster currently are those named "Lurrus of the Dream-Den" (there are multiple versions).

### The "average balanced power" is used in the prompt and is mentioned in the business information as a formula that takes into consideration a card's power (only for numeric values) and rarity, giving a higher value to rare cards, but the exact formula is not specified.

The average balanced power is calculated as the average of power*rarity, where "rarity" is worth 1 for uncommon and common cards, and 2 for rare and mythic cards.

### The cards table has columns named info*, which makes it impossible to know wich one mentions if a card is foiled or not

The column info6 from the cards table is the definitive column for determining whether a card is foiled or not. It has a value of 1 if foiled and 0 if not foiled.

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
