#!/usr/bin/env python3
"""Run the fast deterministic regression checks without loading TTS models or Cargo."""
from __future__ import annotations

import subprocess
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
CHECKS = (
    "test_bootstrap.py",
    "test_tts_core.py",
    "test_audio_metrics.py",
    "test_quarian_filter_core.py",
    "test_quarian_cleanup.py",
    "test_mcp_schema.py",
    "test_mcp_tool_errors.py",
)


def main() -> None:
    for filename in CHECKS:
        print(f"==> {filename}", flush=True)
        subprocess.run([sys.executable, str(ROOT / "tests" / filename)], cwd=ROOT, check=True)
    print(f"PASS: {len(CHECKS)} fast regression checks completed without model or Cargo loading.")


if __name__ == "__main__":
    main()
