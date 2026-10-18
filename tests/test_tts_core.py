#!/usr/bin/env python3
"""Unit checks for phase-2 validation, splitting, and WAV-format helpers."""
from __future__ import annotations

import sys
import tempfile
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))

import numpy as np
import soundfile as sf

from audio import validate_pcm16_mono_wav
from errors import InvalidWavError, ToolInputError
from tts import split_tts_text, validate_tts_input


def expect(exception: type[Exception], callback: object) -> None:
    try:
        callback()  # type: ignore[operator]
    except exception:
        return
    raise AssertionError(f"Expected {exception.__name__}")


def main() -> None:
    chunks = split_tts_text("  One.\nTwo and three.  ", maximum=8)
    assert chunks == ["One.", "Two and", "three."], chunks

    long_word_chunks = split_tts_text("abcdefghijkl", maximum=5)
    assert long_word_chunks == ["abcde", "fghij", "kl"], long_word_chunks
    assert all(len(chunk) <= 5 for chunk in long_word_chunks)

    assert validate_tts_input("Valid Spanish text.", "ef_dora", 1.0) == ("es", "ef_dora")
    assert validate_tts_input("Valid English text.", None, 1.0, "en") == ("en_us", "af_heart")
    assert validate_tts_input("Valid English text.", None, 1.0, "en-us") == ("en_us", "af_heart")
    expect(ToolInputError, lambda: validate_tts_input("", "ef_dora", 1.0))
    expect(ToolInputError, lambda: validate_tts_input("text", "not_a_voice", 1.0))
    expect(ToolInputError, lambda: validate_tts_input("text", "ef_dora", 1.0, "en_us"))
    expect(ToolInputError, lambda: validate_tts_input("text", "af_heart", 1.0, "es"))
    expect(ToolInputError, lambda: validate_tts_input("text", None, 1.0, "fr"))
    expect(ToolInputError, lambda: validate_tts_input("text", "ef_dora", True))
    expect(ToolInputError, lambda: validate_tts_input("text", "ef_dora", 1.31))

    with tempfile.TemporaryDirectory() as directory:
        valid = Path(directory) / "valid.wav"
        sf.write(valid, np.zeros(240, dtype=np.float32), 24_000, subtype="PCM_16", format="WAV")
        metadata = validate_pcm16_mono_wav(valid)
        assert metadata.sample_rate == 24_000 and metadata.channels == 1 and metadata.frames == 240

        incompatible = Path(directory) / "incompatible.wav"
        sf.write(incompatible, np.zeros(240, dtype=np.float32), 22_050, subtype="PCM_16", format="WAV")
        expect(InvalidWavError, lambda: validate_pcm16_mono_wav(incompatible))

    print("PASS: phase-2 TTS validation, chunking, and WAV helpers.")


if __name__ == "__main__":
    main()
