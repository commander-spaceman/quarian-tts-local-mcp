#!/usr/bin/env python3
"""Manual in-memory MCP check that invokes the single real Quarian TTS tool."""
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
        response = await client.call_tool(
            "generate_quarian_audio",
            {"text": "Hola. Esta es una prueba MCP de voz quariana.", "voice": "ef_dora", "speed": 1.0},
        )
    text = "\n".join(getattr(part, "text", "") for part in response.content)
    assert not response.is_error, text
    assert text.startswith("Generated Quarian WAV audio: "), text
    print(f"PASS: {text}")


if __name__ == "__main__":
    asyncio.run(main())
