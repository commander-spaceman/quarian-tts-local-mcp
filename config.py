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
KOKORO_HOME = MODELS / "kokoro" / "huggingface"
KOKORO_MODEL_DIR = MODELS / "kokoro" / "source"

# Kokoro creates/reads its Hugging Face cache only beneath this checkout. These
# values must be set before importing Kokoro or Hugging Face modules.
os.environ.setdefault("HF_HOME", str(KOKORO_HOME))
os.environ.setdefault("HUGGINGFACE_HUB_CACHE", str(KOKORO_HOME / "hub"))
os.environ.setdefault("TOKENIZERS_PARALLELISM", "false")
os.environ.setdefault("OMP_NUM_THREADS", str(max(1, min(6, os.cpu_count() or 1))))

# These folders are intentionally local to this project. Model weights and audio
# results are ignored by Git; their empty placeholders are versioned instead.
for directory in (MODELS, OUTPUTS, LOGS, KOKORO_HOME):
    directory.mkdir(parents=True, exist_ok=True)

MAX_TEXT_CHARS = 12_000
MAX_AUDIO_BYTES = 100 * 1024 * 1024
DEFAULT_VOICE = "ef_dora"
SPANISH_VOICES = frozenset({"ef_dora", "em_alex", "em_santa"})
SAMPLE_RATE = 24_000
