#!/usr/bin/env python3
"""
MCP tool CLI - calls FastMCP streamable-http tools from the terminal.

Usage:
  python /usr/local/bin/mcp <server_url> <tool_name> [<json_args>]

Examples:
  python /usr/local/bin/mcp http://sql-tools:8000/mcp execute_sql '{"query": "SELECT COUNT(*) FROM cards"}'
  python /usr/local/bin/mcp http://sql-tools:8000/mcp get_database_info '{"database_name": "card_games"}'
  python /usr/local/bin/mcp http://business-info:8000/mcp get_business_info '{"database_name": "card_games", "search_string": "modern era definition"}'
  python /usr/local/bin/mcp http://ask-human:8000/mcp ask_human '{"question": "What does modern era mean?"}'
  python /usr/local/bin/mcp http://sql-tools:8000/mcp submit_sql '{"query": "SELECT COUNT(*) FROM cards WHERE ..."}'
"""
from __future__ import annotations

import json
import sys
import urllib.request
import urllib.error


def call_mcp_tool(base_url: str, tool_name: str, arguments: dict) -> str:
    headers_base = {
        "Content-Type": "application/json",
        "Accept": "application/json, text/event-stream",
    }

    # Step 1: initialize
    init_payload = json.dumps({
        "jsonrpc": "2.0",
        "id": 0,
        "method": "initialize",
        "params": {
            "protocolVersion": "2024-11-05",
            "capabilities": {},
            "clientInfo": {"name": "mcp-cli", "version": "1.0"},
        },
    }).encode()

    req = urllib.request.Request(base_url, data=init_payload, headers=headers_base, method="POST")
    try:
        with urllib.request.urlopen(req, timeout=30) as resp:
            session_id = resp.headers.get("Mcp-Session-Id")
            _body = resp.read().decode("utf-8", errors="replace")
    except urllib.error.HTTPError as e:
        error_body = e.read().decode("utf-8", errors="replace")
        print(f"Initialize failed ({e.code}): {error_body}", file=sys.stderr)
        sys.exit(1)

    # Step 2: tool call
    call_headers = dict(headers_base)
    if session_id:
        call_headers["Mcp-Session-Id"] = session_id

    call_payload = json.dumps({
        "jsonrpc": "2.0",
        "id": 1,
        "method": "tools/call",
        "params": {"name": tool_name, "arguments": arguments},
    }).encode()

    req2 = urllib.request.Request(base_url, data=call_payload, headers=call_headers, method="POST")
    try:
        with urllib.request.urlopen(req2, timeout=60) as resp2:
            raw = resp2.read().decode("utf-8", errors="replace")
    except urllib.error.HTTPError as e:
        error_body = e.read().decode("utf-8", errors="replace")
        print(f"Tool call failed ({e.code}): {error_body}", file=sys.stderr)
        sys.exit(1)

    return _extract_text(raw)


def _extract_text(raw: str) -> str:
    """Extract text from SSE data: lines or plain JSON."""
    lines = raw.splitlines()
    texts: list[str] = []
    for line in lines:
        if line.startswith("data: "):
            try:
                data = json.loads(line[6:])
                _collect_content(data, texts)
            except json.JSONDecodeError:
                texts.append(line[6:])
    if texts:
        return "\n".join(texts)
    # fallback: try parsing as plain JSON
    try:
        data = json.loads(raw)
        _collect_content(data, texts)
        return "\n".join(texts) if texts else raw
    except json.JSONDecodeError:
        return raw


def _collect_content(data: dict, out: list[str]) -> None:
    result = data.get("result") or {}
    if isinstance(result, dict):
        for item in result.get("content", []):
            if isinstance(item, dict) and item.get("type") == "text":
                out.append(item["text"])
    error = data.get("error")
    if error:
        out.append(f"ERROR: {error}")


if __name__ == "__main__":
    if len(sys.argv) < 3:
        print(__doc__)
        sys.exit(1)

    server_url = sys.argv[1]
    tool_name = sys.argv[2]
    args_raw = sys.argv[3] if len(sys.argv) > 3 else "{}"

    try:
        arguments = json.loads(args_raw)
    except json.JSONDecodeError:
        print(f"Error: arguments must be valid JSON, got: {args_raw!r}", file=sys.stderr)
        sys.exit(1)

    result = call_mcp_tool(server_url, tool_name, arguments)
    print(result)
