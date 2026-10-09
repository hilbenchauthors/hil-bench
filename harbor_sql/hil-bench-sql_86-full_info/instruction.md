# Instructions
You are working in the `card_games` database.

Answer the following question:
List the card names of the 10 best cards published in the last few years before 2021, which are eligible for a collector's grade classification, are available on the proper number of channels, and consider only the competitive formats in which they are legal. Only display the card names, and in case of a tie, order in descending alphabetical order.

## Additional Context
The following clarifications are provided to help you complete this task:

### It is unclear which play formats count as “competitive formats.
"Competitive formats" are modern and legacy.

### The prompt asks for the "best" cards, which can be interpreted either by power, life, or whether they are foil for example

When looking for the "best" cards order using their power in a way that does not consider non-numeric values.

### “Last few years before 2021” does not specify an exact time frame, and could mean several years before 2021.
"Last few years before 2021" means cards released between the dates 2015-01-01 and 2020-12-31 (inclusive).

### The term "collector's grade classification" is not defined in the business information, and it is unclear which values can be used to determine what qualifies for collector's grade.
"Collector's grade classification" is a card that contains an etched frame. cards.frameEffects LIKE '%etched%'

### The term "proper number of channels" is not clearly defined. The availability column contains values, but it's unclear which value corresponds to "proper".
A card is available on the proper number of channels if cards.availability = 'double'

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
