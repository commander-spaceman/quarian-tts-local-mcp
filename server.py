#!/usr/bin/env python3
"""MCP-over-stdio entry point exposing only the local Quarian TTS tool."""
from __future__ import annotations

from mcp.server.mcpserver import MCPServer

from common import LOG
from mcp_tools import generate_quarian_audio

mcp = MCPServer(
    "quarian-tts-local",
    title="Local Quarian TTS",
    description="Generate local Quarian-filtered WAV audio from text with Kokoro and a CPU DSP filter.",
    instructions=(
        "Use generate_quarian_audio for a new local WAV. It accepts text, an installed "
        "Spanish Kokoro voice, and speed; it returns the absolute output path."
    ),
    log_level="WARNING",
)


mcp.tool()(generate_quarian_audio)


def main() -> None:
    """Run the MCP server exclusively over standard input/output."""
    LOG.info("event=server_start phase=1 transport=stdio")
    mcp.run(transport="stdio")


if __name__ == "__main__":
    main()
