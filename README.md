# Quarian TTS Local MCP

A modular local MCP server that produces WAV audio through this CPU-only flow:

```text
text -> Kokoro TTS -> quarian-voice-filter-cli -> WAV
```

This repository is deliberately limited to Quarian voice generation. It does
not contain and will not add OCR, translation, STT, Ollama, images, or state
from those workflows.

## Current status: phase 5 - testing, operations, and documentation

The stdio MCP server exposes exactly one tool. It loads Kokoro on demand and
runs the Rust `quarian-voice-filter-cli` against its 24 kHz mono PCM16 WAV.
The installation provides model-free regression checks, local diagnostics, and
integration tests with signal metrics. There are no OCR, translation, STT, or
state-reading tools.

```text
quarian-tts-local-mcp/
|-- config.py                # Paths, limits, and local Kokoro cache
|-- common.py                # Logging, metrics, and model/filter locks
|-- errors.py                # Safe typed errors
|-- audio.py                 # PCM16/24 kHz WAV naming, validation, metrics
|-- tts.py                   # Local Kokoro synthesis and sentence chunking
|-- quarian_filter.py        # Safe Rust CLI build and execution
|-- quarian_tts.py           # Kokoro -> filter orchestration and cleanup
|-- mcp_tools.py             # Safe MCP adapter for the only tool
|-- server.py                # Stdio MCP entry point and tool registration
|-- diagnose.py              # Offline local-prerequisite diagnostic
|-- lmstudio-mcp.json.example
|-- models/                  # Future local weights; ignored by Git
|-- outputs/                 # Generated WAV files; ignored by Git
|-- logs/                    # Local server.log; ignored by Git
|-- tests/
|-- pyproject.toml
`-- requirements.txt
```

All Python modules live in the repository root. There is no `src/` directory
and one will not be created.

## Local environment

Python 3.12 or 3.13 is required. Create an isolated environment inside the
project:

```bash
cd /home/juan/Dev/commander-spaceman/quarian-tts-local-mcp
/home/juan/.miniconda3/bin/conda create --prefix "$PWD/.conda" python=3.12 -y
"$PWD/.conda/bin/python" -m pip install --upgrade pip
"$PWD/.conda/bin/python" -m pip install -r requirements.txt
"$PWD/.conda/bin/python" -m pip install --no-deps -e .
"$PWD/.conda/bin/python" -m pip check
```

The requirements pin CPU PyTorch, Kokoro, NumPy, SoundFile, and MCP. They do
not install CUDA or any OCR, STT, translation, or Ollama dependency.

On Ubuntu, install the system libraries used by Kokoro and SoundFile:

```bash
sudo apt install espeak-ng libsndfile1
```

## Local Kokoro weights

Synthesis reads local weights only and does not download models during an MCP
call. The following structure must exist:

```text
models/kokoro/source/
|-- config.json
|-- kokoro-v1_0.pth
`-- voices/
    |-- ef_dora.pt
    |-- em_alex.pt           # Optional, needed only when selected
    `-- em_santa.pt          # Optional, needed only when selected
```

To reuse an existing copy without duplicating it:

```bash
mkdir -p models/kokoro
ln -s /home/juan/ai-models/Kokoro-82M models/kokoro/source
```

Alternatively, download the public weights once outside an MCP call:

```bash
.conda/bin/hf download hexgrad/Kokoro-82M --local-dir models/kokoro/source
```

`models/` is ignored by Git. Accepted voices are `ef_dora`, `em_alex`, and
`em_santa`; selecting an accepted voice that is absent from disk fails clearly.

## Local paths

By default, the project root is this checkout. An administrator can move the
data root by setting `QUARIAN_TTS_ROOT` before starting the process. Derived
paths are:

- `models/`: local weights;
- `outputs/`: final WAVs and temporary intermediate WAVs;
- `logs/server.log`: rotating log that never uses stdout.

MCP parameters cannot change these paths.

## Local Quarian filter

The adapter uses the documented CLI from this local checkout:

```text
/home/juan/Dev/commander-spaceman/quarian-voice-filter
```

Rust/Cargo 1.96 or later is required. On its first run, the adapter builds only
the `quarian-voice-filter-cli` package with one Cargo job. Downloads and build
artifacts stay in `.quarian-cargo/` and `.quarian-filter-build/`; neither is
versioned and the external checkout is never modified.

An administrator can override locations and limits before starting the process:

- `QUARIAN_FILTER_REPOSITORY`: alternate local checkout;
- `QUARIAN_FILTER_BIN`: already-built executable that skips compilation;
- `QUARIAN_FILTER_TIMEOUT_SECONDS`: execution limit, default `120`;
- `QUARIAN_FILTER_BUILD_TIMEOUT_SECONDS`: build limit, default `600`.

They are not MCP parameters. Input and output are validated before and after
calling the CLI; both must be 24 kHz mono PCM16 WAVs. Every execution uses a
new name, never overwrites a result, serializes concurrent filter calls, and
removes the intermediate Kokoro WAV even after an error. Logs include only
metadata, timings, paths, and stderr byte counts, never text or stderr content.

## MCP tool

| Tool | Parameters | Result |
|---|---|---|
| `generate_quarian_audio` | required `text`; `voice="ef_dora"`; `speed=1.0` | New absolute Quarian WAV path in `outputs/` |

`text` accepts up to 12,000 characters. `voice` must be `ef_dora`, `em_alex`,
or `em_santa` and must exist locally. `speed` must be between `0.7` and `1.3`.
The response includes the path, duration, sample rate, and selected voice, but
never repeats submitted text. Input, weight, filter, build, and timeout errors
are returned through safe messages.

## LM Studio

Do not overwrite your complete configuration. Add or replace only the
`quarian-tts-local` entry from
[`lmstudio-mcp.json.example`](lmstudio-mcp.json.example) in the LM Studio MCP
configuration. After reloading MCP, exactly one tool should appear:
`generate_quarian_audio`.

## Operational diagnostic

Before connecting LM Studio, inspect prerequisites without loading Kokoro,
building Rust, or generating audio:

```bash
.conda/bin/python diagnose.py
# After installing the editable project:
quarian-tts-diagnose
```

The report ends in `READY` only when it finds a supported interpreter, Python
dependencies, writable directories, local weights and voice, plus either a
built Quarian CLI or a checkout and Cargo ready to build it. It does not show
user text, tokens, or audio content. Resolve every `MISSING` line before
starting LM Studio.

Results, weights, Cargo caches, and logs remain local and are ignored by Git.
WAV files may contain sensitive content; delete them manually when they are no
longer needed.

## Tests and regression checks

The fast suite is deterministic and does not load weights, Kokoro, or Cargo:

```bash
.conda/bin/python -m compileall -q audio.py common.py config.py diagnose.py errors.py tts.py quarian_filter.py quarian_tts.py mcp_tools.py server.py
.conda/bin/python tests/run_core_checks.py
.conda/bin/python -m pip check
```

It covers MCP startup and the single-tool schema, input limits, text chunking,
WAV format and metrics, filter-error classification, and intermediate-file
cleanup. The output lists each test and ends with the total number of completed
checks.

After preparing local weights, run the CPU integration checks. They create
unique WAVs in `outputs/`; each verifies its header, finite samples, positive
peak, and positive RMS:

```bash
# Kokoro only.
.conda/bin/python tests/test_kokoro_synthesis.py

# Kokoro followed by the Quarian filter; also verifies the bytes changed.
.conda/bin/python tests/test_quarian_synthesis.py

# The same synthesis invoked through an in-memory MCP client.
.conda/bin/python tests/test_mcp_quarian_tool.py
```

The limits are 12,000 characters, speeds from `0.7` to `1.3`, and chunks up to
800 characters split preferentially at sentence boundaries. Model and filter
operations are serialized within the process, and synthesized text is never
logged.

## Listening review and troubleshooting

Headers and signal metrics prove technical integrity, not perceived quality.
Listen to a short sample after changing versions, voices, or local parameters.
Check intelligibility, missing segments, saturation or clipping, and the
expected Quarian effect. Open a generated result with:

```bash
xdg-open outputs/quarian_audio_YYYYMMDD_HHMMSS_microseconds_UUID.wav
```

To investigate an operation, inspect only local metadata:

```bash
tail -n 80 logs/server.log
.conda/bin/python diagnose.py
.conda/bin/python -m pip check
```

- If weights or a voice are missing, repair `models/kokoro/source/` and run the
  diagnostic again.
- If Cargo or the checkout is missing, install Rust 1.96+, configure
  `QUARIAN_FILTER_REPOSITORY`, or use `QUARIAN_FILTER_BIN`.
- If the filter exhausts resources or times out, reduce the text, close
  memory-heavy processes, and adjust timeouts only as an administrator before
  starting the server.
- If LM Studio does not discover the tool, check the paths in
  `lmstudio-mcp.json.example`, reload MCP, and confirm the diagnostic is
  `READY`.

`server.py` is an MCP stdio server. Running it directly waits for protocol
messages and does not open a terminal user interface.
