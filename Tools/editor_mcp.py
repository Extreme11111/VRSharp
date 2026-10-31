"""Invoke the local editor tool through the official MCP client and stdio transport."""
import asyncio
import json
from pathlib import Path
import sys
from mcp import ClientSession, StdioServerParameters
from mcp.client.stdio import stdio_client


async def main():
    failed = False
    server = str(Path(__file__).with_name("editor_mcp_server.py"))
    async with stdio_client(StdioServerParameters(command=sys.executable, args=[server])) as streams:
        async with ClientSession(*streams) as session:
            await session.initialize()
            result = await session.call_tool("run_editor_script", {"script": sys.argv[1]})
            for block in result.content:
                if block.type == "text":
                    data = json.loads(block.text)
                    print(data.get("output", ""))
                    if not data.get("success"):
                        print(data.get("traceback", block.text), file=sys.stderr)
                        failed = True
    return 1 if failed else 0


if __name__ == "__main__":
    sys.exit(asyncio.run(main()))
