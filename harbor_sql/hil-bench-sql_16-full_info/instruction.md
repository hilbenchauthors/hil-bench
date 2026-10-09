# Instructions
You are working in the `formula_1` database.

Answer the following question:
Provide the distinct constructorId values for all constructors that are currently classified as championship front-runners, have competed across the premier circuit set, exhibit an attrition finish pattern, satisfy the qualifying dominance score criterion, and meet the internal visibility classification requirement based on the visibility_code field in the constructors table.

## Additional Context
The following clarifications are provided to help you complete this task:

### The phrase “currently classified as championship front-runners” depends on a classification that can change outside the dataset and is not encoded in the database.
Interpret “currently classified as championship front-runners” using an externally provided roster snapshot expressed as an explicit allowlist of constructors.constructorRef. Include only constructors whose constructorRef is in: {'mclaren', 'williams', 'renault', 'ferrari', 'red_bull', 'jordan', 'footwork'}.

### “attrition finish pattern” is vague: “attrition” is not precisely defined, and there are several plausible options as to which race results should be treated as attrition versus non-attrition.
Measure attrition using status.status: a result counts as attrition if status.status is not 'Finished' and is not a classified finish of the form '+N Lap' or '+N Laps'; compute attrition_rate = attrition_events / total_results per constructor, considering only constructors with at least 100 rows in results. Interpret the requirement as belonging to the lower-attrition tier, defined by attrition_rate <= median(attrition_rate) (lower median via ROW_NUMBER() ordering by attrition_rate ASC, constructorId ASC).

### The term “premier circuit set” is not defined, and there is no built-in field that labels circuits as premier.
Define the “premier circuit set” as the set of races.circuitId values that served as a season opener (i.e., races.round = 1) at least 5 times in the dataset. A constructor satisfies the requirement if it has results on at least 3 distinct circuits from that set (counted via COUNT(DISTINCT races.circuitId) after joining results --> races).

### “qualifying dominance score” is undefined; it is unclear which qualifying fields to use, how to compute the score, and what cutoff qualifies as “dominant.”
Compute dominance_score per constructor from qualifying as the proportion of qualifying rows where qualifying.position is non-NULL and <= 3, divided by the constructor’s total qualifying rows. Consider only constructors with at least 40 qualifying rows. Interpret the criterion as membership in the top quartile, defined by dominance_score >= Q3(dominance_score) where Q3 is selected via ROW_NUMBER() ordering by dominance_score ASC, constructorId ASC and taking row ((3*n + 3)/4).

### The column constructors.visibility_code exists but its meaning is unclear; the schema only states it is an internal reporting code without specifying interpretation or ordering.
Interpret the “internal visibility classification requirement” as belonging to the most frequent visibility_code value(s) in constructors: compute code counts over non-empty visibility_code, select the maximum count, and include all codes tied for that maximum frequency. A constructor satisfies the requirement if its visibility_code is in that set.

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
