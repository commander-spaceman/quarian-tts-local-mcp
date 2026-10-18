"""Errors with messages safe to return from a future MCP tool."""
from __future__ import annotations


class QuarianTTSError(RuntimeError):
    """Base error for this local text-to-speech project."""


class ToolInputError(QuarianTTSError, ValueError):
    """The supplied TTS text, voice, or speed is invalid."""


class KokoroModelUnavailable(QuarianTTSError):
    """Required local Kokoro model or voice files are absent."""


class InvalidWavError(QuarianTTSError):
    """A WAV is unsafe, unreadable, or outside the required interchange format."""
