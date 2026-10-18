#!/usr/bin/env python3
"""Check MCP adapter input failures without loading Kokoro or the Rust CLI."""
from __future__ import annotations

import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))

from mcp_tools import generate_quarian_audio


def main() -> None:
    assert generate_quarian_audio("", "ef_dora", 1.0) == "There is no text to synthesize."
    assert generate_quarian_audio("text", "unknown_voice", 1.0).startswith("Unsupported voice for es.")
    assert generate_quarian_audio("text", "ef_dora", 1.0, "en_us").startswith("Unsupported voice for en_us.")
    assert generate_quarian_audio("text", None, 1.0, "fr") == "Unsupported language. Available languages: es, en, en_us."
    assert generate_quarian_audio("text", "ef_dora", 1.4) == "Speed must be between 0.7 and 1.3."
    print("PASS: MCP adapter returns safe validation failures without model loading.")


if __name__ == "__main__":
    main()
