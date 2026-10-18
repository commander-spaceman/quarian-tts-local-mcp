#!/usr/bin/env python3
"""MCP-over-stdio entry point for the local Quarian TTS service.

Phase 1 deliberately registers no tools.  Later phases add the single Quarian
TTS tool without changing the process entry point or transport.
"""
from __future__ import annotations

from mcp.server.mcpserver import MCPServer

from common import LOG

mcp = MCPServer(
    "quarian-tts-local",
    title="Local Quarian TTS",
    description="Local text-to-speech service for Quarian-filtered WAV audio.",
    instructions="This server is being prepared. No tools are registered in phase 1.",
    log_level="WARNING",
)


def main() -> None:
    """Run the MCP server exclusively over standard input/output."""
    LOG.info("event=server_start phase=1 transport=stdio")
    mcp.run(transport="stdio")


if __name__ == "__main__":
    main()
