# Instructions
You are working in the `california_schools` database.

Answer the following question:
List the names of virtual special education schools identified as Virtual code F that opened in or after 2022, are overcrowded and have an average earlyl level SAT reading score lower than 50 on the most recent SAT cycle available up to today

## Additional Context
The following clarifications are provided to help you complete this task:

### The term “special education school” is underspecified because it can reasonably include different special-education categories (e.g., public special education schools, nonpublic special education schools, district consortia special education schools). Without specifying which categories are intended, the set of eligible schools is ambiguous and materially changes the results.
Define “special education school”: Use frpm."Educational Option Type" and include only these exact values:
- Special Education School
- Nonpublic Special Education School
- District Consortia Special Education School
(No substring matching; exact equality only.)

### The question asks for “the most recent SAT cycle available up to today,” but the database provides no cycle/year field for SAT results, so determining what qualifies as “most recent up to today” requires external information about the SAT reporting cycle / dataset release date that is not stored in the DB.
Assume the satscores table is the most recent SAT snapshot available “up to today,” and that this snapshot corresponds to a SAT cycle ending on 2024-06-30. Only schools that were already open on or before 2024-06-30 are eligible to be evaluated for SAT in this task; therefore, include the filter date(schools.OpenDate) <= '2024-06-30' in addition to date(schools.OpenDate) >= '2022-01-01'.

### SAT section scores (Reading/EBRW component) are commonly on a 200–800 scale, so “average < 50” contradicts real-world scoring. The question uses a Reading SAT threshold of 50, which contradicts the real SAT section scoring scale (minimum ~200). 
Use 450 as the intended cutoff: filter schools with AvgScrRead < 450.

###  “Overcrowded” is required as a filter but is not defined anywhere, and the database contains no direct capacity/overcrowding indicator.
Define “overcrowded” as:
Use frpm."Enrollment (K-12)" only (not Ages 5–17). For each school (CDSCode), use the most recent frpm."Academic Year" available for that CDSCode. A school is “overcrowded” if frpm."Enrollment (K-12)" > 3000. If a school has no frpm record, exclude it from results (cannot evaluate overcrowding).

### The question requires early level SAT reading averages, yet satscores does not have a clear definition on how to determine which scores are early level
Use rtype = 'S' as the only early level SAT rows.

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
