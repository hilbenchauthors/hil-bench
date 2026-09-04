# Instructions
You are working in the `california_schools` database.

Answer the following question:
What is the total number of non-chartered schools in the d1 region with a cleaned proportion (0–1) of eligible free meals for grades 1 through 12 that is less than 0.18? Show me their average cleaned proportion (0–1), their average SAT score in math, and how many of them earned an award over the last few weeks.


## Additional Context
The following clarifications are provided to help you complete this task:

### The phrase “over the last few weeks” is ambiguous in both (a) the window length (how many weeks counts as “few”) and (b) the anchor date (relative to today vs relative to the latest award date available in the dataset). This ambiguity changes how many schools are counted as having earned an award.
Interpret “last few weeks” as a 7-week (49-day) rolling window ending on the latest available schools.last_award_earning_date in the database (2026-01-31). Count a school as “earned an award in the last few weeks” if last_award_earning_date is between 2025-12-14 and 2026-01-31 (inclusive).

### The question filters for “schools in the d1 region”, but schools.Regions contains multiple inconsistent codes that could plausibly represent “d1” (e.g., D01, D001, d01, d-1, etc.). It’s unclear which exact values should be treated as the “d1 region”, and different choices materially change the school set and all aggregates.

Interpret “d1 region” as only schools.Regions IN ('d-1','d01') (exact match), excluding all other region variants.

### The business info says to multiply by an “appropriate correction constant,” but it does not define what “appropriate” means (e.g., it could depend on reporting standard, year, or grade-span convention). Multiple correction constants could plausibly be used, and choosing a different one changes which schools fall below the threshold.

Use a correction constant of 2.4 when computing the cleaned percent:
cleaned_free_pct = (free_meal_count / enrollment) * 2.4.

### The satscores table stores section-level SAT averages in columns AvgScr1–AvgScr5, but the table definition does not specify which AvgScr* corresponds to the Math section. Because multiple AvgScr* columns look like plausible SAT section scores, it’s unclear which one should be used for “average SAT score in math.”
Use satscores.AvgScr3 as the average SAT Math score.

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
