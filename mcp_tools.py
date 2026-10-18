"""MCP-safe adapter functions for the Quarian TTS core."""
from __future__ import annotations

import time
from typing import Annotated

from pydantic import Field

from common import LOG, log_result
from config import DEFAULT_LANGUAGE
from errors import QuarianTTSError, ToolInputError
from quarian_tts import generate_quarian_wav


TextInput = Annotated[
    str,
    Field(description="Text to synthesize locally. Maximum 12000 characters."),
]
VoiceInput = Annotated[
    str | None,
    Field(description="Optional voice compatible with language; omit it to select the language default."),
]
LanguageInput = Annotated[
    str,
    Field(
        description=(
            "Synthesis language. Use exactly one of: es, en, en_us, or en-us. "
            "For English, prefer the JSON value \"en\"; do not include quote "
            "marks, commas, or other punctuation in the value."
        ),
        json_schema_extra={"enum": ["es", "en", "en_us", "en-us"]},
    ),
]
SpeedInput = Annotated[
    float,
    Field(ge=0.7, le=1.3, description="Speech speed from 0.7 through 1.3."),
]


def generate_quarian_audio(
    text: TextInput,
    voice: VoiceInput = None,
    speed: SpeedInput = 1.0,
    language: LanguageInput = DEFAULT_LANGUAGE,
) -> str:
    """Generate one local Quarian-filtered PCM WAV from Spanish or English text."""
    started = time.monotonic()
    try:
        result = generate_quarian_wav(text, voice, speed, language)
        log_result(
            "generate_quarian_audio",
            started,
            "ok",
            filter="quarian-voice-filter-cli",
            language=result.language,
            voice=result.voice,
            tts_seconds=f"{result.tts_seconds:.3f}",
            filter_seconds=f"{result.filter_seconds:.3f}",
            audio_seconds=f"{result.audio.duration_seconds:.3f}",
            output=result.audio.path,
        )
        return (
            f"Generated Quarian WAV audio: {result.audio.path} "
            f"({result.audio.duration_seconds:.1f} seconds, 24 kHz, "
            f"language {result.language}, voice {result.voice})."
        )
    except ToolInputError as exc:
        log_result(
            "generate_quarian_audio",
            started,
            "input_error",
            filter="quarian-voice-filter-cli",
            language=language,
            voice=voice,
        )
        return str(exc)
    except QuarianTTSError as exc:
        log_result(
            "generate_quarian_audio",
            started,
            "error",
            filter="quarian-voice-filter-cli",
            language=language,
            voice=voice,
            error=type(exc).__name__,
        )
        return f"Quarian audio generation failed: {exc}"
    except Exception as exc:
        # Do not log the exception string/traceback: a third-party library could
        # include source text in it. The error class is sufficient for diagnosis.
        LOG.error("tool=generate_quarian_audio status=error error=%s", type(exc).__name__)
        log_result(
            "generate_quarian_audio",
            started,
            "error",
            filter="quarian-voice-filter-cli",
            language=language,
            voice=voice,
            error=type(exc).__name__,
        )
        return "Quarian audio generation failed. Review logs/server.log."
