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


class ExternalRepositoryUnavailable(QuarianTTSError):
    """The configured Quarian Rust checkout is absent or incomplete."""


class QuarianDependencyError(QuarianTTSError):
    """Cargo or a configured Quarian executable cannot be used."""


class QuarianBuildError(QuarianTTSError):
    """The Quarian CLI compilation failed."""


class QuarianFilterTimeout(QuarianTTSError):
    """Building or executing the filter exceeded its configured timeout."""


class QuarianResourceError(QuarianTTSError):
    """The external process likely exhausted CPU or memory resources."""


class QuarianFilterError(QuarianTTSError):
    """The external filter returned a non-resource processing error."""
