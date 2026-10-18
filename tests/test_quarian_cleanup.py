#!/usr/bin/env python3
"""Regression check: failed or successful orchestration never retains its intermediate WAV."""
from __future__ import annotations

import sys
from pathlib import Path
from unittest.mock import patch

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))

import numpy as np
import soundfile as sf

from audio import new_wav_path, validate_pcm16_mono_wav
from config import OUTPUTS
from quarian_tts import generate_quarian_wav
from tts import KokoroSynthesis


def fake_create_wav(*_args: object, **_kwargs: object) -> KokoroSynthesis:
    target = new_wav_path("cleanup_input")
    sf.write(target, np.full(240, 0.1, dtype=np.float32), 24_000, subtype="PCM_16", format="WAV")
    return KokoroSynthesis(audio=validate_pcm16_mono_wav(target), chunks=1)


def fake_apply_filter(source: Path, target: Path) -> float:
    samples, rate = sf.read(source, dtype="float32")
    sf.write(target, -samples, rate, subtype="PCM_16", format="WAV")
    return 0.001


def main() -> None:
    before = set(OUTPUTS.glob(".quarian_input_*.wav"))
    result = None
    with patch("quarian_tts.create_wav", fake_create_wav), patch("quarian_tts.apply_quarian_filter", fake_apply_filter):
        result = generate_quarian_wav("synthetic cleanup check")
    try:
        assert result.intermediate_path is None, result
        assert result.audio.path.is_file(), result.audio.path
        assert set(OUTPUTS.glob(".quarian_input_*.wav")) == before
    finally:
        if result is not None:
            result.audio.path.unlink(missing_ok=True)
    print("PASS: Quarian orchestration removes its temporary Kokoro input by default.")


if __name__ == "__main__":
    main()
