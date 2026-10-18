"""Shared logging primitives for the Quarian TTS MCP server."""
from __future__ import annotations

import logging
from logging.handlers import RotatingFileHandler

from config import LOGS


LOG = logging.getLogger("quarian_tts_mcp")
LOG.setLevel(logging.INFO)
LOG.propagate = False

if not LOG.handlers:
    handler = RotatingFileHandler(
        LOGS / "server.log",
        maxBytes=2 * 1024 * 1024,
        backupCount=3,
        encoding="utf-8",
    )
    handler.setFormatter(logging.Formatter("%(asctime)s %(levelname)s %(message)s"))
    LOG.addHandler(handler)
