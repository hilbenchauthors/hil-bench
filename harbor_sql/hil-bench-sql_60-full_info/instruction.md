# Instructions
You are working in the `thrombosis_prediction` database.

Answer the following question:
What percentage of patients whose examinations report leg-related symptoms, whose admission was followed at the outpatient clinic, and with selected elevated antibody measurements developed thrombosis?


## Additional Context
The following clarifications are provided to help you complete this task:

### The question asks to filter patients based on the presence of a symptom term, but it does not specify how symptom values should be matched, leaving it unclear whether the filter requires an exact match, partial match, synonymous terms, or semantic interpretations of the symptom text, according to the multiple possibilities that exist in the symptoms column.
Symptom filtering is resolved by applying an exact text match to 'pain in leg' in the Symptoms field.

### The question refers to “elevated antibody measurements” without specifying which antibodies are clinically relevant or which variables should be used, allowing multiple valid interpretations that lead to different calculations.
Selected antibody measurements are antibody_2 (anti-cardiolipin IgG) and antibody_3 (anti-cardiolipin IgM), with elevated values defined as greater than 0. A patient meets the antibody criterion if either antibody_2 or antibody_3 is greater than 0, treating NULL

### The business information provides categorical thrombosis labels without explaining their meaning, ordering, or relationship to clinical outcomes, making it unclear how thrombosis presence should be determined.


Thrombosis presence is defined as records where the Thrombosis value equals 'K'

### The Patient table contains multiple admission-related columns with identical value domains and no documented distinction, making it unclear which column should be used to determine admission status for filtering or analysis.

Admission status for the analysis is determined exclusively using the Admission_2 column, not Admission_1, nor Admission_3.

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
