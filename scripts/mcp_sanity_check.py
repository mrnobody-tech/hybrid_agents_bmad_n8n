"""Quick sanity check that the MCP server is reachable.

Usage:
    poetry run python scripts/mcp_sanity_check.py

Relies on the same environment variables as the main application.
"""

from __future__ import annotations

import json

from mcp_client import MCPClient, MCPClientError


def main() -> None:
    client = MCPClient.from_env()
    if not client:
        print("MCP client not configured. Set N8N_MCP_URL and MCP_AUTH_TOKEN.")
        return

    print(f"Running MCP sanity check (mode={client.mode})")
    try:
        init = client.initialize({"name": "sanity-check", "version": "0.1"})
        print("- initialize ->", json.dumps(init.result, indent=2))

        tools = list(client.list_tools())
        print(f"- tools/list -> {len(tools)} tools available")
        if tools:
            names = [t['name'] for t in tools]
            print(f"  Tools: {', '.join(names)}")
            if client.mode == "simulation":
                # Use a known fixture shape
                result = client.call_tool_text('get_node_essentials', {'nodeType': 'nodes-base.httpRequest'})
                print(f"- tools/call(get_node_essentials) -> {result[:120]}...")
            else:
                print("  (Real mode: tools/call not executed in sanity script)")
    except MCPClientError as exc:
        print(f"MCP sanity check failed: {exc}")


if __name__ == "__main__":
    main()
