#!/usr/bin/env python3
"""Manual in-memory MCP check that invokes the single real Quarian TTS tool."""
from __future__ import annotations

import argparse
import asyncio
import re
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))

from audio import measure_pcm16_mono_wav
from mcp import Client
from server import mcp


async def run(text_input: str, language: str, voice: str | None, speed: float) -> None:
    arguments: dict[str, object] = {"text": text_input, "language": language, "speed": speed}
    if voice is not None:
        arguments["voice"] = voice
    async with Client(mcp) as client:
        response = await client.call_tool("generate_quarian_audio", arguments)
    text = "\n".join(getattr(part, "text", "") for part in response.content)
    assert not response.is_error, text
    match = re.fullmatch(
        rf"Generated Quarian WAV audio: (.+) \([0-9.]+ seconds, 24 kHz, language {re.escape(language)}, voice .+\)\.",
        text,
    )
    assert match, text
    output = Path(match.group(1))
    metrics = measure_pcm16_mono_wav(output, label="MCP result")
    assert metrics.finite and metrics.rms > 0.0, metrics
    print(f"PASS: {text} peak={metrics.peak:.6f}, RMS={metrics.rms:.6f}.")


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--text", default="Hello. This is an American English Quarian voice MCP test.")
    parser.add_argument("--language", choices=("es", "en_us"), default="en_us")
    parser.add_argument("--voice", default=None)
    parser.add_argument("--speed", type=float, default=1.0)
    args = parser.parse_args()
    asyncio.run(run(args.text, args.language, args.voice, args.speed))


if __name__ == "__main__":
    main()
