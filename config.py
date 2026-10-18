"""Paths and process-wide settings for the local Quarian TTS MCP server.

Only administrator-controlled environment variables are read here; MCP requests
never choose filesystem locations.
"""
from __future__ import annotations

import os
from pathlib import Path


ROOT = Path(os.environ.get("QUARIAN_TTS_ROOT", Path(__file__).resolve().parent)).expanduser().resolve()
MODELS = ROOT / "models"
OUTPUTS = ROOT / "outputs"
LOGS = ROOT / "logs"

# These folders are intentionally local to this project.  Model weights and audio
# results are ignored by Git; their empty placeholders are versioned instead.
for directory in (MODELS, OUTPUTS, LOGS):
    directory.mkdir(parents=True, exist_ok=True)
