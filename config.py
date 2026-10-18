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
DEFAULT_LANGUAGE = "es"
DEFAULT_VOICES = {
    "es": "ef_dora",
    "en_us": "af_heart",
}
LANGUAGE_PIPELINE_CODES = {
    "es": "e",
    "en_us": "a",
}
LANGUAGE_ALIASES = {
    "es": "es",
    "en_us": "en_us",
    "en-us": "en_us",
}
LANGUAGE_VOICES = {
    "es": frozenset({"ef_dora", "em_alex", "em_santa"}),
    "en_us": frozenset({"af_heart"}),
}
# Kept as a compatibility alias for callers that omit language selection.
DEFAULT_VOICE = DEFAULT_VOICES[DEFAULT_LANGUAGE]
SAMPLE_RATE = 24_000

# The Rust filter is an administrator-configured local executable/check-out, not
# an MCP parameter. Its build downloads and artifacts remain inside this project.
DEFAULT_QUARIAN_REPOSITORY = Path("/home/juan/Dev/commander-spaceman/quarian-voice-filter")
QUARIAN_REPOSITORY = Path(
    os.environ.get("QUARIAN_FILTER_REPOSITORY", str(DEFAULT_QUARIAN_REPOSITORY))
).expanduser().resolve()
QUARIAN_BUILD_DIR = ROOT / ".quarian-filter-build"
QUARIAN_CARGO_HOME = ROOT / ".quarian-cargo"
QUARIAN_FILTER_NAME = "quarian-voice-filter-cli"
QUARIAN_FILTER_BIN = os.environ.get("QUARIAN_FILTER_BIN")
FILTER_TIMEOUT_SECONDS = float(os.environ.get("QUARIAN_FILTER_TIMEOUT_SECONDS", "120"))
BUILD_TIMEOUT_SECONDS = float(os.environ.get("QUARIAN_FILTER_BUILD_TIMEOUT_SECONDS", "600"))
