# Instructions
You are working in the `thrombosis_prediction` database.

Answer the following question:
What is the average core enzymatic indicator for patients in the sustained engagement cohort, considering only laboratory entries where the patient simultaneously presents elevated protein markers and protein values within the standard reference range? Include only patients whose initial assessment record falls between 1991 and 1995.

## Additional Context
The following clarifications are provided to help you complete this task:

### The phrase "core enzymatic indicator" is ambiguous because it could refer to a single enzyme's raw measurement, a composite score combining several enzyme values, or a clinically derived ratio between enzymes.
Interpret "core enzymatic indicator" as the alkaline phosphatase (ALP) measurement; compute AVG(ALP) across qualifying laboratory records, rounded to 4 decimal places.

### The question requires laboratory entries where the patient shows both "elevated protein markers" and "protein values within the standard reference range," which are mutually contradictory statements about protein levels.
Interpret "elevated protein markers" as TP (total protein) > 8.5 and "protein values within the standard reference range" as ALB (albumin) between 3.5 and 5.5 inclusive.

### The business information defines "sustained engagement cohort" using qualitative language ("meaningful and continuous relationship," "documented interaction history") that cannot be directly translated into a precise SQL filter.
Interpret "sustained engagement cohort" as patients who have at least 68 laboratory records in the database, i.e., COUNT of rows in the Laboratory table grouped by patient ID >= 68.

### The Patient table contains four date columns: Description, First Date, Registration Date, and Referral Date,  and the question's reference to "initial assessment record" does not clarify which column should be used for the date range filter.
Interpret "initial assessment record" as the "Referral Date" column in the Patient table. Filter patients whose Referral Date falls between '1991-01-01' and '1995-12-31' inclusive.

# Available Commands
The following commands are installed in this terminal — run them directly from the shell.
**Only run ONE command per turn** — each command blocks until the MCP server responds.
- `get_database_info thrombosis_prediction` — list all tables and their descriptions
- `get_table_info thrombosis_prediction <table>` — list columns and descriptions for a table
- `get_column_info thrombosis_prediction <table> <column>` — get details for a specific column
- `get_business_info thrombosis_prediction "<question>"` — semantic search over business documentation
- `execute_sql "<query>"` — execute a SQL query against the database
- `submit_sql "<query>"` — submit your final SQL answer

# Submission Instructions
When you are confident your SQL query is correct, call the `submit_sql` tool with your final query as the argument. If you do not call `submit_sql`, the task will be considered incomplete and scored as 0.
