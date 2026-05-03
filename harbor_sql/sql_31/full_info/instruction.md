# Instructions
You are working in the `california_schools` database.

Answer the following question:
What are the names and high academic performance scores of the 3 oldest schools in Maricopa County that have fewer test takers than students scoring above 1500 and offer exclusively virtual instruction?

## Additional Context
The following clarifications are provided to help you complete this task:

### The question asks for schools in "Maricopa County," but Maricopa County does not exist in California. Maricopa County is located in Arizona (where Phoenix is located). California has "Mariposa County" which sounds similar but is a different county. This contradicts real-world geographic facts about California counties.
Use "Mariposa County" which is the correct California county name. The query should filter for schools in Mariposa County, California, ignoring the "Maricopa County" specification which refers to an Arizona county not present in the California dataset.

### The requirement "have fewer test takers than students scoring above 1500" is logically impossible. Students scoring above 1500 (NumGE1500) are a subset of total test takers (NumTstTakr). It is mathematically impossible for the total number of test takers to be less than the number of high-scoring students.
Ignore the "fewer test takers than students scoring above 1500" condition entirely, as it describes a mathematically impossible scenario where a subset would be larger than the total.

### The term "oldest schools" can be interpreted in multiple valid ways. It could mean schools with the earliest opening date (OpenDate), schools with the lowest CDS code (CDSCode), or schools with the smallest NCES identifier. Without clarification, different interpretations will yield different results.
"Oldest schools" should be determined by sorting schools by CDSCode in ascending order. The schools with the lowest CDSCode values are considered the oldest.

### The question asks for "high academic performance" but does not define how this metric should be calculated. There are multiple SAT score columns available (Reading, Math, Writing), but it's unclear whether to use an average, a sum, a weighted combination, or another formula.
"High academic performance" should be calculated as the average of the three SAT subject scores: (AvgScrRead + AvgScrMath + AvgScrWrite) / 3.

### The question asks for schools that "offer exclusively virtual instruction," but the Virtual column contains coded values (A, B, C, D) without clear definitions. It's unclear which value or values represent "exclusively virtual" instruction versus other types of virtual or non-virtual offerings.
"Exclusively virtual instruction" corresponds to Virtual = 'C', which indicates schools with no physical building where all instruction is virtual. Schools with other Virtual codes (A, B, D) should be excluded.

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
