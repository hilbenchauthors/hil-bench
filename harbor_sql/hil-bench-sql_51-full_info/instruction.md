# Instructions
You are working in the `card_games` database.

Answer the following question:
Among cards with special frame effects released before 1992 during the spring season, show me the ID of the top 5 competitive cards ordered by those with the most design variations.

## Additional Context
The following clarifications are provided to help you complete this task:

### The question asks for cards released before 1992 during the spring season. However, Magic: The Gathering was first published in August 1993, so no cards exist before that date.
Magic: The Gathering was first published in 1993. Treat "before 1992 during the spring season" as "Spring 1994" (the first spring season since the game's release) and filter for cards from sets with releaseDate >= '1994-03-01' AND releaseDate < '1994-06-01'.

### The question asks for cards with "special frame effects", but it is unclear which specific frameEffects values should be considered as special.
The following frameEffects values count as special: extendedart and etched.

### The business information defines "competitive cards" as those with strong tournament performance, but this definition is vague and does not specify how to identify them from the database.
Competitive cards are defined as those with rarity 'mythic' or 'rare' and a convertedManaCost between 4 and 5.

### The question asks to order by "design variations", but the cards table has three similar columns (variations_standard, variations_premium, variations_base) with descriptions mentioning different weight factors (standard, premium, base), making it unclear how to combine them to calculate design variations.
Design variations is calculated using a weighted formula: (variations_standard * 2 + variations_premium * 3 + variations_base) / 6

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
