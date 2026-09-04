# Instructions
You are working in the `thrombosis_prediction` database.

Answer the following question:
List the ID and sex of patients with LDH beyond normal range who went to the hospital in the many first years of the 1990s.


## Additional Context
The following clarifications are provided to help you complete this task:

### The question asks for patients who went to the hospital in "the many first years of the 1990s" but does not specify how many years constitute "the first years." It is unclear whether this means the first 2 years (1990-1991), first 3 years (1990-1992), first 4 years (1990-1993), or some other timeframe.
"The many first years of the 1990s" means 1990 through 1997 inclusive. Filter for patients where the date is between '1990-01-01' and '1997-12-31'.

### The business information defines "LDH beyond normal range" as "lactate dehydrogenase values demonstrating deviation from normative enzymatic activity baselines, indicating metabolic marker elevation exceeding acceptable clinical boundaries," but this definition is vague and does not specify the actual threshold value or numeric criterion for determining when LDH is beyond normal range.
LDH beyond normal range refers to LDH > 500. Filter for patients where LDH > 500 in the Laboratory table.

### The Patient table contains multiple date columns (Date1, Date2, Date3, Date4) all with the same vague description "patient timeline marker," but the table definition does not explain what each date represents or which date field corresponds to hospital visits. The table's multi-date structure is confusing and makes it unclear which column to use for filtering patients by hospital visit dates.
Date3 represents the date when the patient first went to the hospital. Use Date3 to filter for hospital visits. Date1 is the patient's birthday, Date2 is the first recorded data date, and Date4 is an additional timeline marker.

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
