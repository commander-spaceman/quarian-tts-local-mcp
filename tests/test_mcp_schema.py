#!/usr/bin/env python3
"""Verify phase 4 exposes precisely one typed MCP tool without loading models."""
from __future__ import annotations

import asyncio
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))

from mcp import Client
from server import mcp


async def main() -> None:
    async with Client(mcp) as client:
        tools = await client.list_tools()

    assert len(tools.tools) == 1, tools.tools
    tool = tools.tools[0]
    assert tool.name == "generate_quarian_audio", tool.name
    schema = tool.input_schema
    assert set(schema.get("properties", {})) == {"text", "voice", "speed", "language"}, schema
    assert schema.get("required") == ["text"], schema
    assert schema["properties"]["speed"].get("minimum") == 0.7, schema
    assert schema["properties"]["speed"].get("maximum") == 1.3, schema
    assert schema["properties"]["language"].get("default") == "es", schema
    print("PASS: MCP exposes only generate_quarian_audio with the expected schema.")


if __name__ == "__main__":
    asyncio.run(main())
