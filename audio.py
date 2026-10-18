"""WAV naming and validation for the fixed Kokoro interchange format."""
from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime
from pathlib import Path
from uuid import uuid4

from config import MAX_AUDIO_BYTES, OUTPUTS, SAMPLE_RATE
from errors import InvalidWavError


@dataclass(frozen=True)
class WavMetadata:
    """Verified properties of a generated local WAV."""

    path: Path
    duration_seconds: float
    frames: int
    sample_rate: int
    channels: int


@dataclass(frozen=True)
class SignalMetrics:
    """Basic decoded-signal checks intended for local regression diagnostics."""

    samples: int
    finite: bool
    peak: float
    rms: float


def new_wav_path(prefix: str = "kokoro_audio") -> Path:
    """Create a unique final WAV path directly inside the output directory."""
    filename = f"{prefix}_{datetime.now().strftime('%Y%m%d_%H%M%S_%f')}_{uuid4().hex[:8]}.wav"
    return OUTPUTS / filename


def ensure_output_target(path: Path) -> None:
    """Reject output paths that escape outputs/ or would overwrite a file."""
    if path.parent.resolve() != OUTPUTS.resolve() or path.exists() or path.is_symlink():
        raise InvalidWavError("The WAV result path must be a new regular file directly inside outputs/.")


def validate_pcm16_mono_wav(path: Path, *, label: str = "audio") -> WavMetadata:
    """Validate the 24 kHz mono PCM16 format shared by Kokoro and the filter."""
    import soundfile as sf

    if not path.is_file() or path.is_symlink():
        raise InvalidWavError(f"The {label} WAV is missing or is not a regular file.")
    size = path.stat().st_size
    if size == 0 or size > MAX_AUDIO_BYTES:
        raise InvalidWavError(f"The {label} WAV is empty or exceeds the local audio-size limit.")
    try:
        info = sf.info(path)
    except (OSError, RuntimeError, ValueError) as exc:
        raise InvalidWavError(f"The {label} WAV cannot be decoded by soundfile.") from exc
    if (
        info.format != "WAV"
        or info.subtype != "PCM_16"
        or info.samplerate != SAMPLE_RATE
        or info.channels != 1
        or info.frames <= 0
    ):
        raise InvalidWavError(f"Expected a non-empty PCM16 mono {SAMPLE_RATE // 1000} kHz {label} WAV.")
    return WavMetadata(
        path=path,
        duration_seconds=float(info.duration),
        frames=int(info.frames),
        sample_rate=int(info.samplerate),
        channels=int(info.channels),
    )


def measure_pcm16_mono_wav(path: Path, *, label: str = "audio") -> SignalMetrics:
    """Decode a validated WAV and report finite/peak/RMS signal diagnostics."""
    import numpy as np
    import soundfile as sf

    metadata = validate_pcm16_mono_wav(path, label=label)
    try:
        samples, sample_rate = sf.read(path, dtype="float32", always_2d=False)
    except (OSError, RuntimeError, ValueError) as exc:
        raise InvalidWavError(f"The {label} WAV could not be decoded for signal analysis.") from exc
    if sample_rate != metadata.sample_rate or samples.ndim != 1 or len(samples) != metadata.frames:
        raise InvalidWavError(f"The {label} WAV changed or has an unexpected decoded layout.")
    finite = bool(np.isfinite(samples).all())
    if not finite:
        raise InvalidWavError(f"The {label} WAV contains non-finite samples.")
    return SignalMetrics(
        samples=len(samples),
        finite=finite,
        peak=float(np.max(np.abs(samples))),
        rms=float(np.sqrt(np.mean(np.square(samples, dtype=np.float64)))),
    )
