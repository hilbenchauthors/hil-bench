# Instructions
You are working in the `thrombosis_prediction` database.

Answer the following question:
Provide a list of IDs from patients with a positive CRP and high-risk thrombosis that where diagnosed with SLE or BEHCET.

## Additional Context
The following clarifications are provided to help you complete this task:

### The question requires a “positive CRP" but the column contains values like '+','+-','value+','++' and it's unclear which values are considered positive.
Consider positive any value of Laboratory.CRP containing a plus sign anywhere (LIKE %+%) or the value 'POS'.

### The question asks for high-risk thrombosis and the business information is vague as it as patients with notable coagulation markers. 'Notable' is undefined and there are multiple coagulation markers available.
Filter for Examination.Patients thrombosis equal to 1 and values of PT higher or equal than 14 AND values of APTT higher or equal than 45.

### There are multiple columns with diagnosis with values 1 and 0 and there's no information in the schema that shows which values refers to SLE or BEHCET.
Identify patients with SLE using the Patient.DX3 = 1 and BEHCET using the Patient.DX6 equal to 1.

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
