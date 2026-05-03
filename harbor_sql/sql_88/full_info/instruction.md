# Instructions
You are working in the `formula_1` database.

Answer the following question:
Which competitive constructors had drivers with intermediate race negative performance during the Monaco Grand Prix in the last few years before 2015, excluding results affected by critical powertrain failures? Provide their name and registry ID.


## Additional Context
The following clarifications are provided to help you complete this task:

### The phrase "in the last few years before 2015" lacks a precise time boundary. It's unclear whether "few" refers to 2 years, 3 years, or some other span leading up to 2015.
The "last few years before 2015" refers to the period from 2009 through 2014 (inclusive).

### The term "critical powertrain failures" is vague, as the status table contains many different types, and it's unclear which specific statuses qualify.
Critical powertrain failures refer to the following statuses: 'Engine', 'Gearbox', 'Transmission', 'Hydraulics', and 'Electrical'.

### The business information does not clarify what "intermediate race negative performance" means, as standardized positional metrics could refer to grid position, finishing position, or lap-by-lap position.
Intermediate race negative performance refers to drivers who held positions between 12 and 17 during any lap of the Monaco Grand Prix races in the specified timeframe.

### The term "competitive constructors" is not defined in the business information, making it unclear which constructors qualify or what threshold determines competitiveness.
Competitive constructors are those whose drivers have achieved at least 5 first-place finishes (position = 1) recorded in the results table.

### The question asks for the "registry ID", but the constructor_registry table contains multiple ID fields, and it's unclear which column represents the registry ID.
The registry ID refers to the Paddock_ID column in the constructor_registry table.

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
