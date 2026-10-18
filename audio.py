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
