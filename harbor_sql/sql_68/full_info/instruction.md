# Instructions
You are working in the `formula_1` database.

Answer the following question:
Among all constructors that competed in the Singapore Grand Prix between 1995 and 2000 and were able to finish the races, identify those that demonstrated High-Velocity Execution. Consider only constructors whose drivers experienced collisions or accidents, regardless of whether they finished the race. List their identification and indicate whether they are competing in the current Formula One season. Sort the results in descending order by their identification.


## Additional Context
The following clarifications are provided to help you complete this task:

### The question requires determining whether constructors are "competing in the current F1 season," but this depends on real-time information that is not stored in the historical database. The current competitive status changes year by year and cannot be determined from past race data alone.
Constructors competing in the current F1 season are: Alpine, Aston Martin, Williams, Audi, Cadillac, Ferrari, Haas, McLaren, Mercedes, Red Bull, and Racing Bulls. Identify using: WHERE c.name IN ('Alpine', 'Aston Martin', 'Williams', 'Audi', 'Cadillac', 'Ferrari', 'Haas', 'McLaren', 'Mercedes', 'Red Bull', 'Racing Bulls')

### The question asks for "races between 1995-2000 of the Singapore Grand Prix," which is factually impossible because the Singapore Grand Prix was first held in 2008, not in the 1990s. The requested timeframe contradicts the real-life history of this race, making the query unfulfillable as literally stated.
Interpret "races between 1995-2000" as the Singapore Grand Prix races held between 2009 and 2015 (the actual early years of this race). Filter using:WHERE ra.name = 'Singapore Grand Prix'
  AND ra.year BETWEEN 2009 AND 2015

### The question contains contradictory requirements about race completion. It first specifies constructors that "competed...and were able to finish the races" (which requires successful completion), but then states "consider only constructors whose drivers experienced collisions or accidents, regardless of whether they finished the race" (which explicitly includes non-finishers).
To resolve this contradiction, consider constructors that meet BOTH of the following conditions:

The constructor must have at least one result where the status was 'Collision', 'Accident', or 'Spun off' (this satisfies "whose drivers experienced collisions or accidents").
When filtering results for analysis, include results where status = 'Finished' OR status IN ('Collision', 'Accident', 'Spun off') (this satisfies both "able to finish" and "regardless of whether they finished")

### The business information defines "High-Velocity Execution" as "a performance metric that evaluates operational excellence through comparative service interval analytics," but this definition is vague and does not provide measurable criteria. It is unclear how to interpret "operational excellence" and "comparative service interval analytics".
Interpret "operational excellence" as pit stop duration and "comparative service interval analytics" as having an average lower than the global average. Putting them together, High-Velocity Execution means constructors whose average pit stop duration across ALL their pit stops in ALL Singapore Grand Prix races (regardless of year or race outcome) was lower than the overall average pit stop duration across all Singapore Grand Prix races in the database. Calculate using: SELECT r.constructorId, AVG(ps.milliseconds) as constructor_avg
FROM pitStops ps
INNER JOIN races ra ON ps.raceId = ra.raceId
INNER JOIN results r ON ps.raceId = r.raceId AND ps.driverId = r.driverId
WHERE ra.name = 'Singapore Grand Prix'
GROUP BY r.constructorId
HAVING AVG(ps.milliseconds) < (
    SELECT AVG(ps2.milliseconds)
    FROM pitStops ps2
    INNER JOIN races ra2 ON ps2.raceId = ra2.raceId
    WHERE ra2.name = 'Singapore Grand Prix'
)

### The question asks to "list their identification," but the constructors table contains multiple identification fields: constructorId (integer ID), constructorRef (reference name), Acronym (3-letter code), F1_ID (F1 system identifier), DB_ID (database identifier), and Competition_ID (competition system identifier). It is unclear which field represents the canonical "identification" for reporting purposes.
Constructor identification refers to the DB_ID column. Return using: SELECT c.DB_ID

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
