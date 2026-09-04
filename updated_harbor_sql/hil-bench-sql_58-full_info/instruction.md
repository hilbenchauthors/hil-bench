# Instructions
You are working in the `financial` database.

Answer the following question:
How many weekly frequency accounts with problematic loan contracts were issued in the three high-performing districts on the first year that the US had a 5 year long recession? What is the number of problematic-loan weekly account per 1000 residents using the districts' current population? Return the top 3 even if there are no problematic loans along with district name.

## Additional Context
The following clarifications are provided to help you complete this task:

### Is not clear which 'status' value to use for problematic loan. A, B, C or D could be used.
Use B 'status' for a problematic loan.

### The population is data that change over time and requires real time information to resolve it.
Use the following populations:
Hl.m. Praha 1397880
Benesov 103908
Beroun 102562
Kladno 171506
Kolin 108281
Kutna Hora 78565
Melnik 114783
Mlada Boleslav 137726
Nymburk 107638
Praha - vychod 204547
Praha - zapad 161920
Pribram 118285
Rakovnik 56494
Ceske Budejovice 202172
Cesky Krumlov 61655
Jindrichuv Hradec 89564
Pelhrimov 72912
Pisek 72912
Prachatice 51061
Strakonice 69773
Tabor 101363
Domazlice 54391
Cheb 87958
Karlovy Vary 110052
Klatovy 84614
Plzen - mesto 188407
Plzen - jih 68918
Plzen - sever 80666
Rokycany 48770
Sokolov 85200
Tachov 52941
Ceska Lipa 106256
Decin 126294
Chomutov 121480
Jablonec n. Nisou 90569
Liberec 170410
Litomerice 117582
Louny 85381
Most 106773
Teplice 124472
Usti nad Labem 121699
Havlickuv Brod 100000
Hradec Kralove 160000
Chrudim 100000
Jicin 77368
Nachod 112294
Pardubice 92319
Rychnov nad Kneznou 90000
Semily 50000
Svitavy 50000
Trutnov 50000
Usti nad Orlici 50000
Blansko 106884
Brno - mesto 371371
Brno - venkov 203216
Breclav 113842
Hodonin 156524
Jihlava 100000
Kromeriz 108055
Prostejov 110182
Trebic 100000
Uherske Hradiste 144203
Vyskov 89097
Zlin 192639
Znojmo 100000
Zdar nad Sazavou 50000
Bruntal 50000
Frydek - Mistek 50000
Jesenik 50000
Karvina 50000
Novy Jicin 50000
Olomouc 100000
Opava 100000
Ostrava - mesto 300000
Prerov 50000
Sumperk 50000
Vsetin 50000

### The US never had a 5 year long recession. This is contradictory to real life so it is not known which year is being referred to.
Filter the table using the loan.date equal to the year 1998.

### There's no clarification for the term 'High-performing district' and is not clear how to retrieve the metric.
Use the three districts with highest value in district.A15.

### The account.frequency column shows values 'S', 'T' and 'O', 'R', 'Q' with no clear indication on the meaning.
The query should use account.frequency value 'T' to consider weekly frequency accounts.

# Available Commands
The following commands are installed in this terminal — run them directly from the shell.
**Only run ONE command per turn** — each command blocks until the MCP server responds.
- `get_database_info financial` — list all tables and their descriptions
- `get_table_info financial <table>` — list columns and descriptions for a table
- `get_column_info financial <table> <column>` — get details for a specific column
- `get_business_info financial "<question>"` — semantic search over business documentation
- `execute_sql "<query>"` — execute a SQL query against the database
- `submit_sql "<query>"` — submit your final SQL answer

# Submission Instructions
When you are confident your SQL query is correct, call the `submit_sql` tool with your final query as the argument. If you do not call `submit_sql`, the task will be considered incomplete and scored as 0.
