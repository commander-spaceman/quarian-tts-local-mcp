"""CPU-only local Kokoro synthesis; no MCP tool is registered in this phase."""
from __future__ import annotations

import os
import re
from dataclasses import dataclass
from functools import lru_cache
from pathlib import Path
from typing import Any
from uuid import uuid4

from audio import WavMetadata, ensure_output_target, new_wav_path, validate_pcm16_mono_wav
from common import MODEL_LOCK
from config import DEFAULT_VOICE, KOKORO_MODEL_DIR, MAX_TEXT_CHARS, SAMPLE_RATE, SPANISH_VOICES
from errors import KokoroModelUnavailable, ToolInputError

KOKORO_MODEL_NAME = "Kokoro-82M"
KOKORO_REPOSITORY_ID = "hexgrad/Kokoro-82M"
DEFAULT_CHUNK_CHARS = 800


@dataclass(frozen=True)
class KokoroSynthesis:
    """A validated local WAV produced by Kokoro."""

    audio: WavMetadata
    chunks: int


def split_tts_text(text: str, maximum: int = DEFAULT_CHUNK_CHARS) -> list[str]:
    """Split normalized text on sentence boundaries within Kokoro's context size."""
    if maximum < 1:
        raise ValueError("maximum must be a positive integer")
    normalized = re.sub(r"\s+", " ", text).strip()
    if not normalized:
        return []

    sentences = re.split(r"(?<=[.!?;:])\s+", normalized)
    chunks: list[str] = []
    current = ""
    for sentence in sentences:
        while len(sentence) > maximum:
            cut = sentence.rfind(" ", 0, maximum + 1)
            cut = cut if cut > 0 else maximum
            piece = sentence[:cut].strip()
            if current:
                chunks.append(current)
                current = ""
            if piece:
                chunks.append(piece)
            sentence = sentence[cut:].strip()

        proposal = f"{current} {sentence}".strip()
        if current and len(proposal) > maximum:
            chunks.append(current)
            current = sentence
        else:
            current = proposal
    if current:
        chunks.append(current)
    return chunks


def validate_tts_input(text: str, voice: str, speed: float) -> None:
    """Check untrusted input before model loading or filesystem writes."""
    if not isinstance(text, str) or not text.strip():
        raise ToolInputError("There is no text to synthesize.")
    if len(text) > MAX_TEXT_CHARS:
        raise ToolInputError(f"Text exceeds the {MAX_TEXT_CHARS}-character TTS limit.")
    if not isinstance(voice, str) or voice not in SPANISH_VOICES:
        choices = ", ".join(sorted(SPANISH_VOICES))
        raise ToolInputError(f"Unsupported voice. Available Spanish voices: {choices}.")
    if not isinstance(speed, (float, int)) or isinstance(speed, bool) or not 0.7 <= float(speed) <= 1.3:
        raise ToolInputError("Speed must be between 0.7 and 1.3.")


def _model_files() -> tuple[Path, Path]:
    config = KOKORO_MODEL_DIR / "config.json"
    weights = KOKORO_MODEL_DIR / "kokoro-v1_0.pth"
    if not config.is_file() or not weights.is_file():
        raise KokoroModelUnavailable(
            "Local Kokoro weights are unavailable. Prepare models/kokoro/source as documented in README.md."
        )
    return config, weights


@lru_cache(maxsize=1)
def kokoro_pipeline() -> Any:
    """Load the CPU model lazily from local paths, never downloading during a call."""
    from kokoro import KPipeline
    from kokoro.model import KModel

    config, weights = _model_files()
    model = KModel(repo_id=KOKORO_REPOSITORY_ID, config=str(config), model=str(weights)).to("cpu").eval()
    return KPipeline(lang_code="e", repo_id=KOKORO_REPOSITORY_ID, model=model, device="cpu")


def _voice_path(voice: str) -> Path:
    path = KOKORO_MODEL_DIR / "voices" / f"{voice}.pt"
    if not path.is_file():
        raise KokoroModelUnavailable(f"The '{voice}' voice is not available locally.")
    return path


def create_wav(text: str, voice: str = DEFAULT_VOICE, speed: float = 1.0) -> KokoroSynthesis:
    """Synthesize one unique, validated 24 kHz mono PCM16 WAV in outputs/."""
    import numpy as np
    import soundfile as sf

    validate_tts_input(text, voice, speed)
    chunks = split_tts_text(text)
    if not chunks:
        raise ToolInputError("There is no text to synthesize.")
    voice_path = _voice_path(voice)

    parts: list[Any] = []
    silence = np.zeros(int(0.12 * SAMPLE_RATE), dtype=np.float32)
    with MODEL_LOCK:
        pipeline = kokoro_pipeline()
        for index, chunk in enumerate(chunks):
            generated = [np.asarray(result.audio, dtype=np.float32) for result in pipeline(
                chunk,
                voice=str(voice_path),
                speed=float(speed),
                split_pattern=r"\n+",
            )]
            if not generated:
                raise RuntimeError("Kokoro did not return audio samples.")
            if index:
                parts.append(silence)
            parts.extend(generated)

    samples = np.concatenate(parts)
    target = new_wav_path()
    ensure_output_target(target)
    temporary = target.with_name(f".{target.name}.{uuid4().hex}.tmp.wav")
    try:
        sf.write(temporary, samples, SAMPLE_RATE, subtype="PCM_16", format="WAV")
        validate_pcm16_mono_wav(temporary, label="generated")
        os.replace(temporary, target)
    finally:
        temporary.unlink(missing_ok=True)
    return KokoroSynthesis(audio=validate_pcm16_mono_wav(target, label="generated"), chunks=len(chunks))
