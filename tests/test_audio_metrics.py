#!/usr/bin/env python3
"""Unit checks for deterministic PCM signal metrics without loading models."""
from __future__ import annotations

import sys
import tempfile
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))

import numpy as np
import soundfile as sf

from audio import measure_pcm16_mono_wav


def main() -> None:
    with tempfile.TemporaryDirectory() as directory:
        path = Path(directory) / "tone.wav"
        samples = 0.5 * np.sin(2 * np.pi * 440 * np.arange(2_400) / 24_000)
        sf.write(path, samples, 24_000, subtype="PCM_16", format="WAV")
        metrics = measure_pcm16_mono_wav(path, label="test")
    assert metrics.samples == 2_400, metrics
    assert metrics.finite, metrics
    assert 0.49 < metrics.peak <= 0.51, metrics
    assert 0.34 < metrics.rms < 0.37, metrics
    print("PASS: PCM signal metrics report finite peak and RMS values.")


if __name__ == "__main__":
    main()
