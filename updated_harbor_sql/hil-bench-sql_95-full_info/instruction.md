# Instructions
You are working in the `formula_1` database.

Answer the following question:
I want to analyze the circuits where our best races took place. What are the names of the circuits where the 5 best races took place during the classic era? For each circuit, after its name, add columns with a "Yes" or "No" answer to tell me if it is a Grade-A circuit, if its status is active, and if it has a premium track classification.

The final results should be ordered to show the best race first. 

## Additional Context
The following clarifications are provided to help you complete this task:

### The prompt asks for the "best" races, which can be interpreted either by attendance, view count, sales amount, profit margin percentage, or critics score

When looking for the "best" races, look for the races with the highest profit margin percentage (from the profit_margin_percentage in the races table).

### It's unclear what is meant by "Grade-A circuits" as it is not defined anywhere in the schema or business information.
Grade-A circuits are those that have hosted more than 30 Formula 1 races across all seasons. To achieve this, you can use: SELECT circuitId FROM races GROUP BY circuitId HAVING COUNT(*) > 30

### The business info states: "premium track classification indicates circuits that are classified", which is vague and confusing, and doesn't specify how to calculate track classification.
Circuits with premium track classification are those where the average fastest lap speed across all races is below 190 km/h. You can do this using: AVG(CAST(res.fastestLapSpeed AS REAL)) < 190

### It's unknown what the "classic era" means as it is not mentioned anywhere in the schema or business information.
Classic era seasons are years where the final driver's championship point gap between 1st and 2nd was fewer than 15 points. Calculate this by finding the maximum round for each year, then comparing the points of drivers in positions 1 and 2 for that final round. For example:
use: r.year IN (
    SELECT DISTINCT r2.year
    FROM driverStandings ds
    JOIN races r2 ON ds.raceId = r2.raceId
    WHERE ds.position <= 2
        AND r2.round = (SELECT MAX(round) FROM races r3 WHERE r3.year = r2.year)
    GROUP BY r2.year
    HAVING MAX(CASE WHEN ds.position = 1 THEN ds.points END) - MAX(CASE WHEN ds.position = 2 THEN ds.points END) < 15
)

### The circuits table has an operation_status column with numeric values and letters that can not be associated with a specific value. It's unclear which value represents the active status.
Active status is indicated by the values "Disp" or "1" in the operation_status column of the circuits table.

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
