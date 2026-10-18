#!/usr/bin/env python3
"""Offline readiness report for administrators; it never loads models or builds Rust."""
from __future__ import annotations

import importlib.util
import os
import shutil
import subprocess
import sys
from dataclasses import dataclass
from pathlib import Path

from config import (
    DEFAULT_VOICE,
    KOKORO_MODEL_DIR,
    LOGS,
    MODELS,
    OUTPUTS,
    QUARIAN_BUILD_DIR,
    QUARIAN_FILTER_BIN,
    QUARIAN_FILTER_NAME,
    QUARIAN_REPOSITORY,
)


@dataclass(frozen=True)
class Check:
    """One non-sensitive local readiness finding."""

    name: str
    ok: bool
    detail: str


def _cargo_version(cargo: str | None) -> str:
    if not cargo:
        return "not found"
    try:
        completed = subprocess.run(
            [cargo, "--version"],
            stdin=subprocess.DEVNULL,
            stdout=subprocess.PIPE,
            stderr=subprocess.DEVNULL,
            text=True,
            timeout=5,
            check=False,
        )
    except (OSError, subprocess.TimeoutExpired):
        return "unavailable"
    return completed.stdout.strip() if completed.returncode == 0 else "unavailable"


def readiness_checks(voice: str = DEFAULT_VOICE) -> list[Check]:
    """Inspect prerequisites only; this function has no downloads, builds, or TTS."""
    checks: list[Check] = [
        Check("python", sys.version_info[:2] in {(3, 12), (3, 13)}, f"{sys.version.split()[0]}"),
    ]
    for name, directory in (("models", MODELS), ("outputs", OUTPUTS), ("logs", LOGS)):
        checks.append(Check(name, directory.is_dir() and os.access(directory, os.W_OK), str(directory)))

    for module in ("mcp", "kokoro", "numpy", "soundfile", "torch"):
        checks.append(Check(f"python:{module}", importlib.util.find_spec(module) is not None, "installed"))

    config = KOKORO_MODEL_DIR / "config.json"
    weights = KOKORO_MODEL_DIR / "kokoro-v1_0.pth"
    voice_path = KOKORO_MODEL_DIR / "voices" / f"{voice}.pt"
    checks.extend(
        [
            Check("kokoro-config", config.is_file(), str(config)),
            Check("kokoro-weights", weights.is_file(), str(weights)),
            Check("kokoro-voice", voice_path.is_file(), str(voice_path)),
        ]
    )

    configured_binary = Path(QUARIAN_FILTER_BIN).expanduser() if QUARIAN_FILTER_BIN else None
    built_binary = QUARIAN_BUILD_DIR / "release" / QUARIAN_FILTER_NAME
    if configured_binary is not None:
        checks.append(Check("quarian-cli", configured_binary.is_file() and os.access(configured_binary, os.X_OK), str(configured_binary)))
    elif built_binary.is_file() and os.access(built_binary, os.X_OK):
        checks.append(Check("quarian-cli", True, f"built: {built_binary}"))
    else:
        manifest = QUARIAN_REPOSITORY / "Cargo.toml"
        source = QUARIAN_REPOSITORY / "cli" / "src" / "main.rs"
        cargo = shutil.which("cargo")
        checks.extend(
            [
                Check("quarian-checkout", manifest.is_file() and source.is_file(), str(QUARIAN_REPOSITORY)),
                Check("cargo", cargo is not None, _cargo_version(cargo)),
            ]
        )
    return checks


def main() -> None:
    """Print a concise readiness report and return non-zero on a missing requirement."""
    checks = readiness_checks()
    for check in checks:
        status = "OK" if check.ok else "MISSING"
        print(f"{status:<7} {check.name}: {check.detail}")
    if all(check.ok for check in checks):
        print("READY: local Kokoro and Quarian prerequisites are available.")
        return
    print("NOT READY: resolve the MISSING checks; see README.md.")
    raise SystemExit(1)


if __name__ == "__main__":
    main()
