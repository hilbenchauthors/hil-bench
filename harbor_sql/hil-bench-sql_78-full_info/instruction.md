# Instructions
You are working in the `california_schools` database.

Answer the following question:
List the names of schools labeled as locally funded whose disparity is above the locally funded average, but also treat some schools that are below the average as eligible, including only schools with a recorded name and ordering the results alphabetically by school name.

## Additional Context
The following clarifications are provided to help you complete this task:

### The question asks for locally funded schools whose disparity is above the locally funded average, but also states that some schools below the average should be eligible. This creates conflicting eligibility criteria: should eligibility include only schools above the locally funded average, or should it also include some below-average schools, and if so, which ones?
Treat a school as eligible if its disparity is at least the locally funded average, OR if it is the locally funded school whose disparity is the closest value strictly below the locally funded average. If multiple schools tie for being closest below the average, include all tied schools.

### The term “disparity” is confusing because the question does not specify how it should be computed when comparing K–12 enrollment to enrollment ages 5–17. It could reasonably refer to an absolute difference, a ratio, a percentage difference, or another comparison metric.
Compute disparity as the ratio between K–12 enrollment and ages 5–17 enrollment using floating-point division. Exclude rows where either enrollment value is NULL or where the ages 5–17 enrollment value is zero.

### Enrollment values needed to compute disparity appear in multiple plausible sources (e.g., enrollment_metrics, enrollment_metrics_certified, and frpm), and the schema does not specify which source should be treated as authoritative for K–12 enrollment and ages 5–17 enrollment in this calculation.
Use enrollment_metrics_certified as the authoritative data source.

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
