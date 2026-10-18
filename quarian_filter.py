"""Safe local adapter for the external Rust Quarian voice-filter CLI."""
from __future__ import annotations

import os
import shutil
import subprocess
import time
from pathlib import Path
from uuid import uuid4

from audio import ensure_output_target, validate_pcm16_mono_wav
from common import FILTER_LOCK, LOG
from config import (
    BUILD_TIMEOUT_SECONDS,
    FILTER_TIMEOUT_SECONDS,
    QUARIAN_BUILD_DIR,
    QUARIAN_CARGO_HOME,
    QUARIAN_FILTER_BIN,
    QUARIAN_FILTER_NAME,
    QUARIAN_REPOSITORY,
    ROOT,
)
from errors import (
    ExternalRepositoryUnavailable,
    QuarianBuildError,
    QuarianDependencyError,
    QuarianFilterError,
    QuarianFilterTimeout,
    QuarianResourceError,
    QuarianTTSError,
)


def _configured_cli_path() -> Path | None:
    """Return an explicitly configured executable or a previous local build."""
    if QUARIAN_FILTER_BIN:
        candidate = Path(QUARIAN_FILTER_BIN).expanduser()
        if candidate.is_file() and os.access(candidate, os.X_OK):
            return candidate.resolve()
        raise QuarianDependencyError("QUARIAN_FILTER_BIN does not point to an executable Quarian CLI.")

    candidate = QUARIAN_BUILD_DIR / "release" / QUARIAN_FILTER_NAME
    if candidate.is_file() and os.access(candidate, os.X_OK):
        return candidate
    return None


def _cargo_environment() -> dict[str, str]:
    """Keep Cargo downloads and target artifacts scoped to this checkout."""
    environment = os.environ.copy()
    environment.update(
        {
            "CARGO_HOME": str(QUARIAN_CARGO_HOME),
            "CARGO_TARGET_DIR": str(QUARIAN_BUILD_DIR),
            "CARGO_BUILD_JOBS": "1",
            "CARGO_INCREMENTAL": "0",
        }
    )
    return environment


def ensure_quarian_cli() -> Path:
    """Find or lazily build only the documented CPU command-line crate."""
    existing = _configured_cli_path()
    if existing:
        return existing

    manifest = QUARIAN_REPOSITORY / "Cargo.toml"
    cli_source = QUARIAN_REPOSITORY / "cli" / "src" / "main.rs"
    if not manifest.is_file() or not cli_source.is_file():
        raise ExternalRepositoryUnavailable(
            "The quarian-voice-filter checkout or its CLI source is unavailable. "
            "Set QUARIAN_FILTER_REPOSITORY to a valid local checkout."
        )
    cargo = shutil.which("cargo")
    if not cargo:
        raise QuarianDependencyError(
            "Cargo is required to build quarian-voice-filter-cli; install Rust 1.96+ or set QUARIAN_FILTER_BIN."
        )

    QUARIAN_BUILD_DIR.mkdir(parents=True, exist_ok=True)
    QUARIAN_CARGO_HOME.mkdir(parents=True, exist_ok=True)
    command = [
        cargo,
        "build",
        "--manifest-path",
        str(manifest),
        "--package",
        QUARIAN_FILTER_NAME,
        "--release",
        "--target-dir",
        str(QUARIAN_BUILD_DIR),
    ]
    started = time.monotonic()
    try:
        completed = subprocess.run(
            command,
            cwd=QUARIAN_REPOSITORY,
            env=_cargo_environment(),
            stdin=subprocess.DEVNULL,
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            timeout=BUILD_TIMEOUT_SECONDS,
            check=False,
        )
    except subprocess.TimeoutExpired as exc:
        raise QuarianFilterTimeout("Building quarian-voice-filter-cli exceeded the configured timeout.") from exc
    except OSError as exc:
        raise QuarianDependencyError("Cargo could not be started for the Quarian CLI.") from exc

    binary = QUARIAN_BUILD_DIR / "release" / QUARIAN_FILTER_NAME
    if completed.returncode != 0 or not binary.is_file() or not os.access(binary, os.X_OK):
        LOG.warning(
            "operation=ensure_quarian_cli status=build_error returncode=%d stderr_bytes=%d",
            completed.returncode,
            len(completed.stderr),
        )
        diagnostic = completed.stderr[:2048].lower()
        if b"out of memory" in diagnostic or b"cannot allocate memory" in diagnostic:
            raise QuarianResourceError("Building the Quarian CLI ran out of memory; close other applications and retry.")
        raise QuarianBuildError(
            "Could not build quarian-voice-filter-cli. Review the error metadata in logs/server.log."
        )
    LOG.info(
        "operation=ensure_quarian_cli status=ok seconds=%.3f cargo_stderr_bytes=%d binary=%s",
        time.monotonic() - started,
        len(completed.stderr),
        binary,
    )
    return binary


def _classify_filter_failure(returncode: int, stderr: bytes) -> QuarianTTSError:
    diagnostic = stderr[:2048].lower()
    if returncode < 0 or b"out of memory" in diagnostic or b"cannot allocate memory" in diagnostic:
        return QuarianResourceError("The Quarian filter stopped because CPU or RAM resources were exhausted.")
    return QuarianFilterError("The Quarian filter CLI failed; review the error metadata in logs/server.log.")


def apply_quarian_filter(source: Path, target: Path) -> float:
    """Filter a verified WAV into a new output path and return CLI elapsed seconds."""
    validate_pcm16_mono_wav(source, label="source")
    ensure_output_target(target)
    temporary = target.with_name(f".{target.name}.{uuid4().hex}.tmp.wav")
    try:
        with FILTER_LOCK:
            cli = ensure_quarian_cli()
            started = time.monotonic()
            try:
                completed = subprocess.run(
                    [str(cli), "--input", str(source), "--output", str(temporary)],
                    cwd=QUARIAN_REPOSITORY if QUARIAN_REPOSITORY.is_dir() else ROOT,
                    stdin=subprocess.DEVNULL,
                    stdout=subprocess.PIPE,
                    stderr=subprocess.PIPE,
                    timeout=FILTER_TIMEOUT_SECONDS,
                    check=False,
                )
            except subprocess.TimeoutExpired as exc:
                raise QuarianFilterTimeout("The Quarian filter exceeded the configured timeout.") from exc
            except OSError as exc:
                raise QuarianDependencyError("The Quarian filter CLI could not be started.") from exc

        if completed.returncode != 0:
            error = _classify_filter_failure(completed.returncode, completed.stderr)
            LOG.warning(
                "operation=apply_quarian_filter status=cli_error returncode=%d stderr_bytes=%d",
                completed.returncode,
                len(completed.stderr),
            )
            raise error
        validate_pcm16_mono_wav(temporary, label="filtered")
        os.replace(temporary, target)
        return time.monotonic() - started
    finally:
        temporary.unlink(missing_ok=True)
