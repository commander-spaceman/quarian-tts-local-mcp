#!/usr/bin/env python3
"""Unit checks for filter failure classification without invoking Cargo or Kokoro."""
from __future__ import annotations

import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))

from errors import QuarianFilterError, QuarianResourceError
from quarian_filter import _classify_filter_failure


def main() -> None:
    assert isinstance(_classify_filter_failure(1, b"invalid wav"), QuarianFilterError)
    assert isinstance(_classify_filter_failure(-9, b""), QuarianResourceError)
    assert isinstance(_classify_filter_failure(1, b"Cannot allocate memory"), QuarianResourceError)
    print("PASS: phase-3 filter failure classification.")


if __name__ == "__main__":
    main()
