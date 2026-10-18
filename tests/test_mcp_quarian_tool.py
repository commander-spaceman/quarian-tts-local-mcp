#!/usr/bin/env python3
"""Manual in-memory MCP check that invokes the single real Quarian TTS tool."""
from __future__ import annotations

import asyncio
import re
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))

from audio import measure_pcm16_mono_wav
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
    match = re.fullmatch(r"Generated Quarian WAV audio: (.+) \([0-9.]+ seconds, 24 kHz, voice .+\)\.", text)
    assert match, text
    output = Path(match.group(1))
    metrics = measure_pcm16_mono_wav(output, label="MCP result")
    assert metrics.finite and metrics.rms > 0.0, metrics
    print(f"PASS: {text} peak={metrics.peak:.6f}, RMS={metrics.rms:.6f}.")


if __name__ == "__main__":
    asyncio.run(main())
