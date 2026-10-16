# Instructions
You are working in the `formula_1` database.

Answer the following question:
What was the fastest Q1 qualifying time in the British Grand Prix races of the early 2010s among the constructors with the most European-sounding names whose drivers have fiscal residence in Monaco? Only include those whose drivers finished in the most important places from a team points point of view.

## Additional Context
The following clarifications are provided to help you complete this task:

### The question asks for British Grand Prix races in "the early 2010s" but does not specify how many years constitute "early." It is unclear whether this means 2010-2012, 2010-2013, 2010-2014, or another range within the decade.
"Early 2010s" means between January 1, 2010 and June 30, 2012. Filter for races where date BETWEEN '2010-01-01' AND '2012-06-30'.

### The question asks for constructors with "the most European-sounding names" but does not specify which exact constructor name values in the database should be matched as European-sounding. It is unclear whether constructor names like "Ferrari" (Italian-origin word), "Mercedes" (German-origin word), "Williams" (British surname), "Red Bull" (English phrase for Austrian company), "McLaren" (Scottish-origin surname), or other variations qualify, and what specific text patterns or name values count as European-sounding when filtering the constructors.name column.
Filter for constructors where name IN ('Ferrari', 'Toro Rosso', 'Minardi', 'Forti', 'Dallara', 'Andrea Moda', 'Lambo', 'Coloni', 'Osella', 'Alfa Romeo', 'Merzario', 'Maserati', 'Milano').

### The question asks for drivers who finished in "the most important places from a team points point of view" but the business information does not define what constitutes the most important places for team points. It is unclear how many top positions should be considered.
The most important places for team points are the top 7 finishing positions, as these award substantial points compared to the lower scores for positions 8-10. Therefore, filter for results where position <= 7.

### The drivers table contains a fiscal_residence column with numeric coded values (546, 789, 625, 142, 576, 702, 706, 537) but the column description does not explain which country or tax jurisdiction each code represents. It is unclear which code corresponds to Monaco when filtering for drivers with fiscal residence in Monaco.

The fiscal_residence column uses numeric codes where each code represents a different tax jurisdiction. Drivers with fiscal residence in Monaco are identified by the code 775. Filter for drivers where fiscal_residence = 775 to identify drivers with Monaco fiscal residence.

# Available Commands
The following commands are installed in this terminal — run them directly from the shell.
**Only run ONE command per turn** — each command blocks until the MCP server responds.
- `get_database_info formula_1` — list all tables and their descriptions
- `get_table_info formula_1 <table>` — list columns and descriptions for a table
- `get_column_info formula_1 <table> <column>` — get details for a specific column
- `get_business_info formula_1 "<question>"` — semantic search over business documentation
- `execute_sql "<query>"` — execute a SQL query against the database
- `submit_sql "<query>"` — submit your final SQL answer

# Submission Instructions
When you are confident your SQL query is correct, call the `submit_sql` tool with your final query as the argument. If you do not call `submit_sql`, the task will be considered incomplete and scored as 0.
