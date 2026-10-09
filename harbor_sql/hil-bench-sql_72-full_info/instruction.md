# Instructions
You are working in the `card_games` database.

Answer the following question:
What percentage of legal cards from the 29th Core Set have premier certification status and a competitive tournament designation in the commander format that are rare or mythic rare?

## Additional Context
The following clarifications are provided to help you complete this task:

### The question requests cards from the 29th Core Set, but only 24 Core Sets have been released.
Use the cards from the Ninth Edition Core Set: setCode = '9ED'.

### It's unknown what "competitive tournament designation" means, as it is not specified anywhere in the schema or business information.
Competitive tournament designation means cards with cards.edhrecRank <= 5000, and the card must also be legalities.format = 'commander' with legalities.status = 'Legal'.

### It's unclear which value in the certification_status column corresponds to the premier certification status for sets.
Premier certification status refers to sets where certification_status = 'CS2'.

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
