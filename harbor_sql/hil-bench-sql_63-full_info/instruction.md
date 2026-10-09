# Instructions
You are working in the `thrombosis_prediction` database.

Answer the following question:
How many patients with no thrombosis had severe thrombosis outcomes, considering only near-to-adulthood patients who were at the hospital during the course of the three-year period from 1990 to 1993 (inclusive)?

## Additional Context
The following clarifications are provided to help you complete this task:

### The question requires patients to have “no thrombosis” while also having “severe thrombosis outcomes.” These conditions are mutually exclusive if interpreted as applying to the same examination record.
Interpret 'no thrombosis' as the patient's overall latest examination (the chronologically last Examination record for that patient across the entire Examination table, with no date or age filters applied) having Thrombosis = 0. Interpret 'severe thrombosis outcomes' as the patient having at least one record in the Examination table with Thrombosis IN (1, 2), regardless of date range or age at examination.

### Business information defines "near-to-adulthood patients" as patients who are "close to turning 18," but it does not specify how close to 18 a patient must be to qualify.
"near-to-adulthood patients" refers to patients aged between 17 years and 9 months (inclusive) and 18 years (exclusive) at the time of the examination. 

Filter using: 

e."Examination Date" >= DATE(p.Birthday, '+17 years', '+9 months') AND e."Examination Date" < DATE(p.Birthday, '+18 years').

### The phrase "were at the hospital during 1990–1993" is ambiguous because the database has multiple date fields that could represent when a patient was at the hospital, and it is unclear which one to use.
Interpret 'were at the hospital during 1990–1993' as: patients whose First Date in the Patient table falls between 1990-01-01 and 1993-12-31 (inclusive).

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
