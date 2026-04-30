# Instructions
You are working in the `card_games` database.

Answer the following question:
Show me the name and highest collector value of premium foil variant cards with negative mana cost from the reserved list that have been reprinted, ordered by their highest collector value.

## Additional Context
The following clarifications are provided to help you complete this task:

### The question asks for cards with negative mana cost, which contradicts the fundamental rules of Magic: The Gathering where mana costs cannot be negative values. This creates ambiguity about what the user actually wants.
Cards with negative mana cost should be interpreted as artifact cards with convertedManaCost = 0. Filter by convertedManaCost = 0 AND types LIKE '%Artifact%'.

### The question asks for reserved list cards that have been reprinted, which presents contradicting requirements. Cards on the Magic: The Gathering Reserved List are by definition never reprinted, as that is the purpose of the Reserved List policy.
Reserved list cards that have been reprinted refers to reprinted cards from the Reserved List era (pre-2010). Join cards with sets (cards.setCode = sets.code) and filter by isReprint = 1 AND sets.releaseDate < '2010-01-01' AND isPromo = 0. Do not filter by isReserved flag.

### The term "premium foil variants" is not operationally defined in the business context, making it unclear which specific card attributes or combinations qualify a foil card as "premium" versus standard foil printings.
Premium foil variants are defined as cards where hasFoil = 1 AND rarity = 'mythic'. These represent the highest tier of collectible foil cards with mythic rarity.

### The cards table contains three columns (collector_value_1, collector_value_2, collector_value_3) with similar descriptions mentioning different weight factors (standard, premium, base), making it unclear how these values should be combined or which formula to use for calculating the highest collector value metric.
The highest collector value is calculated using a weighted formula: (collector_value_1 * 2 + collector_value_2 * 3 + collector_value_3) / 6. Order results by this calculated value in descending order to show highest values first.

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
