# Instructions
You are working in the `card_games` database.

Answer the following question:
What are the names of the cards that are legal in the pre-modern format, have the ruling "This is a triggered mana ability.", and are standard-issue cards with premium-tier collectible status from heritage-series releases? Order in descending alphabetical order.

## Additional Context
The following clarifications are provided to help you complete this task:

### It's unclear what qualifies as a "standard issue" card, this could refer to first printings, non-promotional printings, or non-alternate art printings.
Standard issue cards are defined as cards where isReprint = 0 in the cards table.

### The business info defines heritage-series releases but does not specify which attribute or value in the database corresponds to this classification.
Heritage-series refers to cards with frameVersion = "1993" in the cards table.

### It's unclear which column contains the information about premium-tier collectible status. The table market_classification contains multiple sources that reference tiers.
The cards that have a premium-tier collectible status are those that have a value greater than or equal to "4" in the investment_tier column in the market_classification table.

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
