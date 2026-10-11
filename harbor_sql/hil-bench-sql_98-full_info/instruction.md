# Instructions
You are working in the `toxicology` database.

Answer the following question:
List all molecules that currently meet the size threshold for enhanced regulatory review, have been flagged as potentially hazardous, and contain a meaningful number of double bonds also having at least 6 connections. For each, show the molecule ID, their hazard indicator, and the double bond count.

## Additional Context
The following clarifications are provided to help you complete this task:

### The question references molecules that "currently meet the size threshold for enhanced regulatory review," but this threshold is set by regulatory bodies, changes periodically, and is not available anywhere in the database or business information.
The size threshold for enhanced review is defined as molecules containing 34 or more atoms. In your SQL, calculate this by counting unique atom_id records per molecule_id (e.g., COUNT(DISTINCT a.atom_id) >= 34).

### The business information defines "meaningful number of double bonds" using qualitative language ("notable unsaturated character," "significant presence") that cannot be directly translated into a numeric SQL threshold.
A "meaningful number" of double bonds is defined as 11 or more. Specifically, filter for bond_type = '=' and ensure the count per molecule is at least 11 (e.g., COUNT(DISTINCT b.bond_id) >= 11).

### The number of connections for molecules "having at least 6 connections." While the 'connected' table is the correct source, its definition "linking two atom identifiers" does not specify its topological data model (for example, direct graph, undirected graph, or multigraph). It is ambiguous how a "connection" is mapped to the columns. "6 connections" could mean 6 total arrows, 6 distinct 'bond_id', or 6 distinct source 'atom_id'. This lack of clear schema definition creates a large search space.
Use the connected table as the authoritative source for structural connections, as it acts as a directed edge list in this schema. Since the connected table represents a directed graph where each connection is defined by a unique source atom, calculate the connection count by counting unique atom_id per molecule (e.g., COUNT(DISTINCT c.atom_id) >=6).

# Available Commands
The following commands are installed in this terminal — run them directly from the shell.
**Only run ONE command per turn** — each command blocks until the MCP server responds.
- `get_database_info toxicology` — list all tables and their descriptions
- `get_table_info toxicology <table>` — list columns and descriptions for a table
- `get_column_info toxicology <table> <column>` — get details for a specific column
- `get_business_info toxicology "<question>"` — semantic search over business documentation
- `execute_sql "<query>"` — execute a SQL query against the database
- `submit_sql "<query>"` — submit your final SQL answer

# Submission Instructions
When you are confident your SQL query is correct, call the `submit_sql` tool with your final query as the argument. If you do not call `submit_sql`, the task will be considered incomplete and scored as 0.
