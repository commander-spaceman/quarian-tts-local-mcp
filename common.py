"""Shared logging primitives for the Quarian TTS MCP server."""
from __future__ import annotations

import logging
import time
from logging.handlers import RotatingFileHandler
from threading import Lock, RLock
from typing import Any

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


# Kokoro uses shared model state. Keep all CPU synthesis operations serialized
# within this MCP process until a future queueing design explicitly changes it.
MODEL_LOCK = RLock()
# The CLI is CPU/RAM intensive and writes a temporary WAV; run one filter at a
# time per MCP process until explicit job scheduling is introduced.
FILTER_LOCK = Lock()


def log_result(operation: str, started: float, status: str, **details: Any) -> None:
    """Log operation metadata and timing without ever logging synthesized text."""
    fields = " ".join(f"{key}={value}" for key, value in details.items() if value is not None)
    LOG.info(
        "operation=%s model=Kokoro-82M status=%s seconds=%.3f %s",
        operation,
        status,
        time.monotonic() - started,
        fields,
    )
