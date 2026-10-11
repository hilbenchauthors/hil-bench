# Instructions
You are working in the `formula_1` database.

Answer the following question:
What is the average top speed for the most popular constructors across European races during the modern era of Formula 1? List each constructor name and their average speed, ordered by average speed from highest to lowest.


## Additional Context
The following clarifications are provided to help you complete this task:

### The term "European races" is underspecified because it could refer to races held in geographically European countries, races in transcontinental countries like Turkey, Russia, or Azerbaijan, or specifically the race named "European Grand Prix" which exists in the database.
European races refer to races held at circuits located in Spain, UK, Italy, Monaco, Germany, Belgium, Hungary, France, Austria, Netherlands, and Portugal.

### The phrase "modern era of Formula 1" does not define a specific start year, as it could refer to various commonly referenced periods such as post-2006 (V8 era), post-2010, or post-2014 (turbo-hybrid era)
The modern era of Formula 1 refers to the period from 2014 onward (the turbo-hybrid era)

### The business information defines "most popular constructors" as those with "strong fan engagement and global brand recognition," but this definition is vague and unmeasurable from the database. 
The most popular constructors are Ferrari, McLaren, Red Bull, Mercedes, Williams, and Renault. Filter using: c.name IN ('Ferrari', 'McLaren', 'Red Bull', 'Mercedes', 'Williams', 'Renault').

### The constructor_race_performance table contains avg_speed, top_speed, and performance_score columns per constructor per race, while the results table contains fastestLapSpeed per driver per race. The question asks for "average top speed" per constructor, which could plausibly map to constructor_race_performance.avg_speed, constructor_race_performance.top_speed, a derivation using constructor_race_performance.performance_score, or an average of results.fastestLapSpeed grouped by constructor. The table definitions do not clarify which metric corresponds to "average top speed" or whether the values are equivalent.
The fastestLapSpeed column in the results table records the fastest lap speed in km/h for each driver in a race. Compute the average top speed per constructor by averaging the fastestLapSpeed values from the results table grouped by constructor.
Before averaging, exclude rows where fastestLapSpeed IS NULL OR fastestLapSpeed = '' OR fastestLapSpeed = '\N'

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
