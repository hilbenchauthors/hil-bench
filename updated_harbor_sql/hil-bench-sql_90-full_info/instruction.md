# Instructions
You are working in the `card_games` database.

Answer the following question:
For cards with infinite power, return the border color of the top 10 cards with the earliest release date. Also, provide their full rarity. Consider only cards with a yellow color indicator (given by the letter "Y") that have a high power (from 5 to 10), disregarding non-numeric values.

## Additional Context
The following clarifications are provided to help you complete this task:

### The prompt asks for cards with a yellow color indicator (given by the letter "Y"), but this is impossible since that color indicator does not exist in MTG

Look for cards with a Black color indicator (given by the letter "B"). They can also have other color indicators, like "B,G"

### The prompt first asks for cards with infinite power, but then requests to only consider cards with power from 5 to 10 and to exclude non-numeric values, which is contradictory.

Only consider cards with power from 5 to infinity (inclusive)

### The "full rarity" term is used in the prompt and is mentioned in the business information as taking into consideration a card's rarity and whether or not it is foil, giving it a ranking from "common" to "ultra-mythic". However, the exact way in which to assing the ranking is not defined, making it confusing.

The full rarity is considered "common" if the card is not foiled, and otherwise by increasing the card's rarity by one, so that a rarity of common becomes uncommon, uncommon becomes rare, rare becomes mythic, and mythic provides ultra-mythic.

### The cards table has columns named borderColor, borderColorText, borderColorFinal, V1BorderColor, SingleBorderColor, and borderColorT, which makes it impossible to know how to obtain a card's border color

The a card's border color given by the column V1BorderColor from the cards table

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
