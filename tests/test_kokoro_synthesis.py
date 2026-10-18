#!/usr/bin/env python3
"""Manual CPU integration check for a real local Kokoro synthesis."""
from __future__ import annotations

import argparse
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))

from audio import measure_pcm16_mono_wav
from tts import create_wav


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--text", default="Hello. This is a short local synthesis test.")
    parser.add_argument("--voice", default="ef_dora")
    parser.add_argument("--speed", type=float, default=1.0)
    args = parser.parse_args()

    result = create_wav(args.text, args.voice, args.speed)
    assert result.audio.path.is_file(), result.audio.path
    assert result.audio.duration_seconds > 0.0, result.audio
    assert result.audio.sample_rate == 24_000 and result.audio.channels == 1, result.audio
    metrics = measure_pcm16_mono_wav(result.audio.path, label="Kokoro result")
    assert metrics.finite and metrics.rms > 0.0, metrics
    print(
        f"PASS: {result.audio.path} - {result.audio.duration_seconds:.2f}s, "
        f"{result.audio.sample_rate} Hz, {result.audio.channels} channel, {result.chunks} chunk(s), "
        f"peak={metrics.peak:.6f}, RMS={metrics.rms:.6f}."
    )


if __name__ == "__main__":
    main()
