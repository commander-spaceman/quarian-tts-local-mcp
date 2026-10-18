#!/usr/bin/env python3
"""Verify the MCP server can negotiate without loading models or the filter."""
from __future__ import annotations

import asyncio
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))

from config import LOGS, MODELS, OUTPUTS
from server import mcp


async def main() -> None:
    from mcp import Client

    for directory in (MODELS, OUTPUTS, LOGS):
        assert directory.is_dir(), directory

    async with Client(mcp) as client:
        tools = await client.list_tools()
    assert [tool.name for tool in tools.tools] == ["generate_quarian_audio"], tools.tools
    print("PASS: MCP server negotiates successfully without loading models or the filter.")


if __name__ == "__main__":
    asyncio.run(main())
