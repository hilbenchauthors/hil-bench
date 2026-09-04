# Instructions
You are working in the `card_games` database.

Answer the following question:
How many modern era cards with vintage edition printing have tournament certified status?

## Additional Context
The following clarifications are provided to help you complete this task:

### The term "modern era" is temporally ambiguous and lacks a specific date range. Without defined start and end dates, the timeframe cannot be accurately determined.
Modern era cards are defined as cards from sets with releaseDate between '2019-01-01' and '2020-12-31' inclusive.

### The business info defines vintage edition printing but does not specify which attribute or value in the database corresponds to this classification.
Vintage edition printing refers to cards with borderColor = "black" in the cards table.

### It's unclear which column(s) contains the information about tournament certified status. The database contains multiple sources that could indicate competitive eligibility classification.
Tournament certified status requires multiple conditions in the tournament_registry table: cert_level = "sanctioned" AND play_tier = 2 AND competition_rank = 4 AND tournament_grade = 3.

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
