# Instructions
You are working in the `card_games` database.

Answer the following question:
I want to see how the mana cost has scaled over the years. Provide the average power and the balanced average mana cost of the cards of the early sets, with that of the cards from the later sets. In the output, call the periods early_sets and later_sets.

## Additional Context
The following clarifications are provided to help you complete this task:

### The prompt asks for the early and later sets, which is underspecified since many sets can be considered as the early or later ones.

The early sets are the first 13 sets that were released. The later sets are the last 7 sets that were released.

### The prompt mentions the "balanced average mana cost", but it is not explained what this term means.

The "balanced average mana cost" counts only colored mana symbols from the manaCost field. These symbols are stored in the format {W}, {U}, {B}, {R}, {G}. Each {W}, {U}, {R}, {G} symbol counts as 1, and each {B} symbol counts as 1.5.

### The "power" column in the "cards" table contains values that are not numeric and can not be interpreted. It is impossible to understand how to use this column to calculate the average power in a set.

In the "power" column in the "cards" table, the values of the form "N+*" (with N being a number) should be considered as N+1. The values "A", "J" and "S" should be considered as 1, 2, and 3 respectively.

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
