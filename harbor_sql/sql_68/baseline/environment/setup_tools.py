"""
Creates bash-callable wrappers for all SQL MCP tools in /usr/local/bin/.
Run once at Docker image build time (via Dockerfile RUN step).

After install, the agent can call tools directly:
  execute_sql "SELECT COUNT(*) FROM cards"
  get_database_info card_games
  get_table_info card_games cards
  get_column_info card_games cards name
  get_business_info card_games "modern era definition"
  ask_human "What does modern era mean?"
  submit_sql "SELECT COUNT(*) FROM cards WHERE ..."
"""
import os

SQL_TOOLS_URL = "http://sql-tools:8000/mcp"
BUSINESS_INFO_URL = "http://business-info:8000/mcp"
ASK_HUMAN_URL = "http://ask-human:8000/mcp"

# (command_name, server_url, tool_name, ordered_param_keys)
# The last key always collects all remaining argv words (handles multi-word queries/questions).
WRAPPERS = [
    ("execute_sql",       SQL_TOOLS_URL,      "execute_sql",       ["query"]),
    ("get_database_info", SQL_TOOLS_URL,       "get_database_info", ["database_name"]),
    ("get_table_info",    SQL_TOOLS_URL,       "get_table_info",    ["database_name", "table_name"]),
    ("get_column_info",   SQL_TOOLS_URL,       "get_column_info",   ["database_name", "table_name", "column_name"]),
    ("get_business_info", BUSINESS_INFO_URL,   "get_business_info", ["database_name", "search_string"]),
    ("ask_human",         ASK_HUMAN_URL,       "ask_human",         ["question"]),
    ("submit_sql",        SQL_TOOLS_URL,       "submit_sql",        ["query"]),
]

TEMPLATE = """\
#!/usr/bin/env python3
import subprocess, sys, json
keys = {keys!r}
args = sys.argv[1:]
params = {{}}
for i, k in enumerate(keys[:-1]):
    params[k] = args[i] if i < len(args) else ""
params[keys[-1]] = " ".join(args[len(keys) - 1:]) if len(args) >= len(keys) else (args[0] if args else "")
subprocess.run(["python", "/usr/local/bin/mcp", {url!r}, {tool!r}, json.dumps(params)])
"""

for name, url, tool, keys in WRAPPERS:
    path = f"/usr/local/bin/{name}"
    with open(path, "w") as f:
        f.write(TEMPLATE.format(keys=keys, url=url, tool=tool))
    os.chmod(path, 0o755)
    print(f"Created {path}")
