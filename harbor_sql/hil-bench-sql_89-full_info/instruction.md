# Instructions
You are working in the `european_football_2` database.

Answer the following question:
Calculate the Robust Agility Score (RAS) of Zlatan Ibrahimovic for the years he played in the Premier League between 2001 and 2004.

## Additional Context
The following clarifications are provided to help you complete this task:

### The question asks for Ibrahimovic’s Premier League years between 2001 and 2004, which contradicts real-life facts (he did not play Premier League matches during that period).
Use Ibrahimovic’s actual Premier League stint only: 2016–2018 (seasons 2016/2017 and 2017/2018).

### The business information states that the Robust Agility Score (RAS) should reduce the impact of “low-quality or atypical assessments” and should include only “adequate rating values,” but it does not define an operational rule for identifying adequate vs. non-adequate assessments (e.g., trimming, winsorization, median, thresholds, completeness rules, etc.). This makes RAS non-computable without clarification.
Compute RAS as a 10% two-sided trimmed mean of the player’s agility rating values within each season/year present in the filtered dataset (after applying the league and time constraints defined elsewhere):
- For each season/year group, collect all agility rating records for the player.
- Sort the agility values and discard the lowest 10% and highest 10%.
- If a season/year has fewer than 10 records, discard only the single minimum and single maximum.
- Compute the arithmetic mean of the remaining values.
- Return one RAS per season/year.

### The Player_Attributes table has all skill attribute columns renamed to numeric identifiers (attr_1, attr_2, attr_3, etc.) without clear explanations of what each number represents. The table definition does not specify which numeric column corresponds to which player skill (crossing, finishing, agility, dribbling, etc.), making it unclear which column to use for filtering by agility.
In the Player_Attributes table, attr_16 represents the agility skill attribute. Use attr_16 to calculate the average agility rating for Zlatan Ibrahimovic.

# Available Commands
The following commands are installed in this terminal — run them directly from the shell.
**Only run ONE command per turn** — each command blocks until the MCP server responds.
- `get_database_info european_football_2` — list all tables and their descriptions
- `get_table_info european_football_2 <table>` — list columns and descriptions for a table
- `get_column_info european_football_2 <table> <column>` — get details for a specific column
- `get_business_info european_football_2 "<question>"` — semantic search over business documentation
- `execute_sql "<query>"` — execute a SQL query against the database
- `submit_sql "<query>"` — submit your final SQL answer

# Submission Instructions
When you are confident your SQL query is correct, call the `submit_sql` tool with your final query as the argument. If you do not call `submit_sql`, the task will be considered incomplete and scored as 0.
