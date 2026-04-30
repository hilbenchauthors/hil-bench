# Instructions
You are working in the `card_games` database.

Answer the following question:
Among the cards that don't have alternative deck limits, could you provide all the rulings received in the recent period for limited-availability cards with a rare layout?

Please provide the name of the card, the layout, the ruling date and the ruling text, in that order.

## Additional Context
The following clarifications are provided to help you complete this task:

### The phrase "recent period" is not specified and could mean different time periods.
Interpret “recent period” as rulings with rulings.date in calendar year 2021 (>= 2021-01-01 and < 2022-01-01).

### It is not clear which value from the column layout to consider as rare, it could be certain layouts or anything distinct than normal.
Interpret "rare layout" as cards with layout equal to 'modal_dfc'.

### There's no clear meaning of the phrase limited availability and multiple columns could be used to calculate the metric.
Consider limited availability the cards with cards.hasFoil equal to 1 and cards.hasNonFoil equal to 0.

### The column AlternativeDeckLimitMarker has confusing values: 7, 17, 27, and 37.
Consider cards with no alternative deck limits as cards for which AlternativeDeckLimitMarker is 17, 27 or 37.

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
