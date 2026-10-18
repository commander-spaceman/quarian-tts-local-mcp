#!/usr/bin/env python3
"""Manual CPU integration test for Kokoro followed by the local Quarian CLI."""
from __future__ import annotations

import argparse
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))

from audio import measure_pcm16_mono_wav
from quarian_tts import generate_quarian_wav


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--text", default="Hello. This is a short Quarian English voice test.")
    parser.add_argument("--language", choices=("es", "en_us"), default="en_us")
    parser.add_argument("--voice", default=None)
    parser.add_argument("--speed", type=float, default=1.0)
    args = parser.parse_args()

    result = None
    try:
        result = generate_quarian_wav(
            args.text,
            voice=args.voice,
            speed=args.speed,
            language=args.language,
            keep_intermediate=True,
        )
        assert result.audio.path.is_file(), result.audio.path
        assert result.intermediate_path is not None and result.intermediate_path.is_file()
        assert result.audio.sample_rate == 24_000 and result.audio.channels == 1, result.audio
        assert result.audio.duration_seconds > 0.0, result.audio
        assert result.audio.path.read_bytes() != result.intermediate_path.read_bytes(), (
            "The Quarian CLI reported success but output bytes match its Kokoro input."
        )
        metrics = measure_pcm16_mono_wav(result.audio.path, label="Quarian result")
        assert metrics.finite and metrics.rms > 0.0, metrics
        print(
            f"PASS: {result.audio.path} - {result.audio.duration_seconds:.2f}s, "
            f"{result.audio.sample_rate} Hz, {result.audio.channels} channel, PCM16, "
            f"language={result.language}, voice={result.voice}, peak={metrics.peak:.6f}, RMS={metrics.rms:.6f}. "
            f"Kokoro={result.tts_seconds:.3f}s, filter={result.filter_seconds:.3f}s, "
            f"total={result.total_seconds:.3f}s."
        )
    finally:
        if result is not None and result.intermediate_path is not None:
            result.intermediate_path.unlink(missing_ok=True)


if __name__ == "__main__":
    main()
