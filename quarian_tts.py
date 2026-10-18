"""Orchestrate local Kokoro synthesis and the Quarian CLI without MCP exposure."""
from __future__ import annotations

import os
import time
from dataclasses import dataclass
from pathlib import Path

from audio import WavMetadata, new_wav_path, validate_pcm16_mono_wav
from common import log_result
from config import DEFAULT_VOICE
from quarian_filter import apply_quarian_filter
from tts import KOKORO_MODEL_NAME, create_wav


@dataclass(frozen=True)
class QuarianSynthesis:
    """Metadata for a completed Kokoro-to-Quarian local conversion."""

    audio: WavMetadata
    tts_seconds: float
    filter_seconds: float
    total_seconds: float
    intermediate_path: Path | None


def generate_quarian_wav(
    text: str,
    voice: str = DEFAULT_VOICE,
    speed: float = 1.0,
    *,
    keep_intermediate: bool = False,
) -> QuarianSynthesis:
    """Generate a filtered WAV and always remove its normal Kokoro input by default."""
    started = time.monotonic()
    created: Path | None = None
    intermediate: Path | None = None
    output: Path | None = None
    tts_seconds = 0.0
    filter_seconds = 0.0
    try:
        tts_started = time.monotonic()
        kokoro = create_wav(text, voice, speed)
        tts_seconds = time.monotonic() - tts_started
        created = kokoro.audio.path

        intermediate = created.with_name(f".quarian_input_{created.stem.split('_')[-1]}.wav")
        os.replace(created, intermediate)
        created = None
        validate_pcm16_mono_wav(intermediate, label="Kokoro input")

        output = new_wav_path("quarian_audio")
        filter_seconds = apply_quarian_filter(intermediate, output)
        audio = validate_pcm16_mono_wav(output, label="filtered")
        result = QuarianSynthesis(
            audio=audio,
            tts_seconds=tts_seconds,
            filter_seconds=filter_seconds,
            total_seconds=time.monotonic() - started,
            intermediate_path=intermediate if keep_intermediate else None,
        )
        log_result(
            "generate_quarian_wav",
            started,
            "ok",
            filter="quarian-voice-filter-cli",
            voice=voice,
            tts_seconds=f"{tts_seconds:.3f}",
            filter_seconds=f"{filter_seconds:.3f}",
            audio_seconds=f"{audio.duration_seconds:.3f}",
            output=audio.path,
        )
        return result
    except Exception as exc:
        log_result(
            "generate_quarian_wav",
            started,
            "error",
            filter="quarian-voice-filter-cli",
            voice=voice,
            tts_seconds=f"{tts_seconds:.3f}",
            filter_seconds=f"{filter_seconds:.3f}",
            error=type(exc).__name__,
            output=output,
        )
        raise
    finally:
        if created is not None:
            created.unlink(missing_ok=True)
        if intermediate is not None and intermediate.exists() and not keep_intermediate:
            intermediate.unlink(missing_ok=True)
