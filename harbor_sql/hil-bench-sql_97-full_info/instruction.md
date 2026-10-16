# Instructions
You are working in the `formula_1` database.

Answer the following question:
Which veteran drivers scored more than 30 points in a single race during the 2016 season? List their last names in ascending alphabetical order, and add a column with their main page.

## Additional Context
The following clarifications are provided to help you complete this task:

### The question asks for drivers who scored more than 30 points in a single race, but the maximum points awarded for a race win in Formula 1 is 25 points (since 2010). Scoring more than 30 points in a single race is impossible.
Interpret "more than 30 points" as scoring the maximum possible points (25 points) in a single race, which corresponds to a race victory.

### The question asks for "veteran drivers" but there is no definition provided in the business information specifying what criteria determines whether a driver is considered a veteran.
A veteran driver is one who has competed in 5 seasons or more (which means 5 different years or more).

### The drivers table has many columns named wikiUrl, principalUrl, introductionUrl, and fanUrl, which makes it impossible to know which one references the main page from these many options

A driver's main page is given by the wikiUrl column in the drivers table

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
