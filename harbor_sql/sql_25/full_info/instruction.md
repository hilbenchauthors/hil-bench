# Instructions
You are working in the `california_schools` database.

Answer the following question:
I want to assess if schools located in a street named after a relevant historic figure have a better performance. From these schools, provide the street name and K-12 enrollment of the top-5 with the best-performing SAT scores. Also, provide a row with the average enrollment per school in Mexico (display it using the street name "Mexico").

## Additional Context
The following clarifications are provided to help you complete this task:

### The prompt looks for "schools located in a street named after a relevant historic figure", but it is unclear which exact values to look for.

When looking for schools located in a street named after a relevant historic figure, only look for streets containing "Martin Luther King Junior", "Jack London", "Grant", "Lafayette", or "Adams".

### The prompt requires to use the average enrollment per school in Mexico, which can not be known unless searched for

The average enrollment per school in Mexico is 110 students

### The business information notes that schools with higher SAT participation may appear stronger due to volume rather than performance quality, creating ambiguity in how participation should influence performance evaluation.
SAT performance must be computed as the average of all three SAT disciplines multiplied by NumGE1500.

### Multiple columns show Sat-lite values and are named AvGScrWrite*, making it imposible to know which one to use
The satscores table is source for SAT performance, using the columns AvgScrMath2, AvgScrRead2, AvgScrWrite2.

# Available Commands
The following commands are installed in this terminal — run them directly from the shell.
**Only run ONE command per turn** — each command blocks until the MCP server responds.
- `get_database_info california_schools` — list all tables and their descriptions
- `get_table_info california_schools <table>` — list columns and descriptions for a table
- `get_column_info california_schools <table> <column>` — get details for a specific column
- `get_business_info california_schools "<question>"` — semantic search over business documentation
- `execute_sql "<query>"` — execute a SQL query against the database
- `submit_sql "<query>"` — submit your final SQL answer

# Submission Instructions
When you are confident your SQL query is correct, call the `submit_sql` tool with your final query as the argument. If you do not call `submit_sql`, the task will be considered incomplete and scored as 0.
