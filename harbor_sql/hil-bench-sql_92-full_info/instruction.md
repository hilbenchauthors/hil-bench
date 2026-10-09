# Instructions
You are working in the `card_games` database.

Answer the following question:
A friend said that the only way for an artist to make good war cards is if they do not finish high school, and I want to prove him wrong. For that, I want the names of the artists who have designed a card that has a military role in its name, has a sanctioned manifest designation, and is currently being featured as one of the "Top Trending Cards" on the MTGGoldfish homepage today. Display the artists' names in descending alphabetical order alongside a "Yes" or "No" column that says whether each artist finished high school or not.


## Additional Context
The following clarifications are provided to help you complete this task:

### The prompt asks for cards that have a military role in its name, but the exact words for which to filter for are not clear.

To look for cards that have a military role in their name, look for names containing the exact words "Knight", "Guard", or "Warrior". This can be looked for using the condition (' ' || c.name || ' ' LIKE '% Knight %'
   OR ' ' || c.name || ' ' LIKE '% Guard %'
   OR ' ' || c.name || ' ' LIKE '% Warrior %'). Looking for other words will produce incorrect results.

### Identifying which card is currently on the MTGGoldfish "Top Trending" list requires access to live, external website data that changes daily and is not stored in the database.
The cards currently featured on the MTGGoldfish "Top Trending" list are 'Serrated Arrows', 'Angel of Mercy', 'Siege-Gang Commander', 'Castle', 'Josu Vess, Lich Knight', 'Clone', 'Mortal Combat', 'Blizzard Knight', 'Tsunami', 'Relentless Assault', 'Infused Arrows', 'Guard Dogs', 'Crusading Knight', 'Stronghold Discipline', 'Frozen Warrior X', 'Mausoleum Guard', 'Obsianus Golem', '	Syr Cadian, Knight Owl', 'Strands of Night', 'Pyre Hound', 'Ma Chao, Western Warrior', 'Sedris, the Traitor King', 'Salvage Titan', 'Godo, Bandit Warlord', 'Goblin Cannon', and 'Fearing Knight'.

### It is unknown what "sanctioned manifest designation" means for cards. This term is not defined in the business information or schema.
Sanctioned manifest designation means cards where convertedManaCost BETWEEN 4 AND 6.

### The "degree" column in the "artists" table contains values that cannot be interpreted as education levels. It is impossible to understand how to use this column to determine if an artist finished high school.

The artists who finished high school are those for whom the "degree" column in the "artists" table contains the values "High" or "Doc". Looking for other values will produce incorrect results.

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
