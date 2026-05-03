# Instructions
You are working in the `california_schools` database.

Answer the following question:
What is the preliminary average number of test takers from Fresno and surrounding schools that opened in the early 1980s?

## Additional Context
The following clarifications are provided to help you complete this task:

### The phrase “Fresno and surrounding schools” is ambiguous because it does not clearly define which locations are included. It is unclear whether “surrounding” refers only to adjacent cities, a specific mileage radius, Fresno County as a whole, or the broader Fresno metropolitan area. Without a precise geographic boundary, the scope of the term is open to multiple interpretations.
Surrounding schools include those in Clovis, Sanger, Madera, and Reedley.

### The phrase “schools that opened in the early 1980s” is ambiguous because the term “early” is not clearly defined. It is unclear which specific years are included, making it uncertain which schools qualify for the analysis and potentially leading to inconsistent interpretations of the data set.
Early 1980s means the year 1980 only (between 1/1/1980 and 12/31/1980)

### The phrase “schools with adequate testing participation” is ambiguous because “adequate” is not defined by any measurable or objective standard. Without a clear threshold or criteria, it is unclear which schools should be included, making the requirement open to interpretation and preventing consistent analysis.
Adequate testing participation means schools with at least 182 test takers

### The satscores table contains multiple plausible “test taker count” fields: NumTstTakr, TestTakerCount, test_taker_reported, test_taker_audited, testtaker_real, final_review_real_test_taker_count with overlapping intent, but the schema/table definition does not specify which field should be treated as the authoritative count for “average number of test takers.” This prevents a consistent calculation.
Use test_taker_audited column from satscores table for test taker counts

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
