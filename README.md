# Quarian TTS Local MCP

A modular local MCP server that produces Quarian-filtered WAV audio through this
CPU-only flow:

```text
text -> Kokoro TTS -> quarian-voice-filter-cli -> WAV
```

It supports Spanish and American English synthesis. This repository is
intentionally limited to Quarian voice generation: it does not include OCR,
translation, STT, Ollama, images, databases, remote inference, or workflow
state from those systems.

## MCP surface

The stdio MCP server exposes exactly one tool:

| Tool | Parameters | Result |
|---|---|---|
| `generate_quarian_audio` | required `text`; `language="es"`; optional `voice`; `speed=1.0` | New absolute Quarian WAV path in `outputs/` |

- Supported languages are `es` (Spanish, the default) and `en_us` (American
  English). The `en-us` alias is also accepted.
- Omitting `voice` selects the default for the selected language: `ef_dora` for
  Spanish or `af_heart` for American English.
- Spanish voices are `ef_dora`, `em_alex`, and `em_santa`. The supported
  American English voice is `af_heart`.
- `voice` must be compatible with `language` and exist as a local Kokoro voice
  file.
- Text is limited to 12,000 characters; speed must be between `0.7` and `1.3`.
- The response includes the absolute path, duration, sample rate, language, and
  selected voice, but never repeats submitted text.

Input, weight, filter, build, and timeout failures are returned through safe
messages. There are no additional MCP tools for OCR, translation, STT, or
saved-state access.

## Structure

```text
quarian-tts-local-mcp/
|-- config.py                # Paths, limits, language/voice configuration
|-- common.py                # Logging, metrics, model/filter locks
|-- errors.py                # Safe typed errors
|-- audio.py                 # PCM16/24 kHz WAV validation and metrics
|-- tts.py                   # Bilingual Kokoro synthesis and chunking
|-- quarian_filter.py        # Safe Rust CLI build and execution
|-- quarian_tts.py           # Kokoro -> filter orchestration and cleanup
|-- mcp_tools.py             # MCP adapter for the single tool
|-- server.py                # Stdio MCP entry point and tool registration
|-- diagnose.py              # Offline local-prerequisite diagnostic
|-- lmstudio-mcp.json.example
|-- models/                  # Local weights; ignored by Git
|-- outputs/                 # Generated WAV files; ignored by Git
|-- logs/                    # Local server.log; ignored by Git
|-- tests/
|-- pyproject.toml
`-- requirements.txt
```

All Python modules live in the repository root. There is no `src/` directory.

## Local environment

Python 3.12 or 3.13 is required. Create an isolated environment in the project:

```bash
cd /home/juan/Dev/commander-spaceman/quarian-tts-local-mcp
/home/juan/.miniconda3/bin/conda create --prefix "$PWD/.conda" python=3.12 -y
"$PWD/.conda/bin/python" -m pip install --upgrade pip
"$PWD/.conda/bin/python" -m pip install -r requirements.txt
"$PWD/.conda/bin/python" -m spacy download en_core_web_sm
"$PWD/.conda/bin/python" -m pip install --no-deps -e .
"$PWD/.conda/bin/python" -m pip check
```

Always use `.conda/bin/python` for this server and its tests. The requirements
pin CPU PyTorch, Kokoro, Misaki's English backend, NumPy, SoundFile, and MCP.
They do not install CUDA or any OCR, STT, translation, or Ollama dependency.

The SpaCy command prepares the American English grapheme-to-phoneme model. It
is required for `en_us`; Spanish synthesis does not use it.

On Ubuntu, install the system libraries used by Kokoro and SoundFile:

```bash
sudo apt install espeak-ng libsndfile1
```

## Local Kokoro weights

Synthesis reads local weights only and never downloads a model during an MCP
call. The following files must exist:

```text
models/kokoro/source/
|-- config.json
|-- kokoro-v1_0.pth
`-- voices/
    |-- ef_dora.pt
    |-- em_alex.pt
    |-- em_santa.pt
    `-- af_heart.pt
```

To reuse an existing local copy without duplicating it:

```bash
mkdir -p models/kokoro
ln -s /home/juan/ai-models/Kokoro-82M models/kokoro/source
```

Alternatively, download public weights once outside an MCP call:

```bash
.conda/bin/hf download hexgrad/Kokoro-82M --local-dir models/kokoro/source
```

`models/` is ignored by Git. An accepted voice whose file is absent from disk
fails clearly before synthesis.

## Local paths and Quarian filter

By default, the project root is this checkout. An administrator can set
`QUARIAN_TTS_ROOT` before starting the process to move local data. The derived
paths are `models/`, `outputs/`, and `logs/server.log`; MCP parameters cannot
change them.

The adapter uses the documented CLI from this local checkout:

```text
/home/juan/Dev/commander-spaceman/quarian-voice-filter
```

Rust/Cargo 1.96 or later is required. On its first call, the adapter builds only
the `quarian-voice-filter-cli` package with one Cargo job. Downloads and build
artifacts stay in `.quarian-cargo/` and `.quarian-filter-build/`; neither is
versioned and the external checkout is never modified.

An administrator can override locations and limits before starting the process:

- `QUARIAN_FILTER_REPOSITORY`: alternate local checkout;
- `QUARIAN_FILTER_BIN`: already-built executable that skips compilation;
- `QUARIAN_FILTER_TIMEOUT_SECONDS`: execution limit, default `120`;
- `QUARIAN_FILTER_BUILD_TIMEOUT_SECONDS`: build limit, default `600`.

They are not MCP parameters. The adapter validates both input and output as
24 kHz mono PCM16 WAVs, creates unique output names, serializes concurrent
filter calls, and removes the intermediate Kokoro WAV even after an error.
Logs include only metadata, timings, paths, and stderr byte counts, never text
or stderr content.

## LM Studio

Do not overwrite your complete configuration. Add or replace only the
`quarian-tts-local` entry from
[`lmstudio-mcp.json.example`](lmstudio-mcp.json.example) in LM Studio's MCP
configuration. Reload MCP afterwards; exactly one tool should appear:
`generate_quarian_audio`.

Example American English request:

```text
Use generate_quarian_audio with text "Hello from my local Quarian voice",
language "en_us", and speed 1.0. Do not set voice; use the default.
```

Example Spanish request:

```text
Use generate_quarian_audio with text "Hola desde mi voz quariana local",
language "es", voice "ef_dora", and speed 1.0.
```

A tool-capable LLM must make separate calls when output is needed in both
languages, because one call produces one WAV.

## Operational diagnostic

Before connecting LM Studio, inspect prerequisites without loading Kokoro,
building Rust, or generating audio:

```bash
.conda/bin/python diagnose.py
# After installing the editable project:
quarian-tts-diagnose
```

The report ends in `READY` only when it finds a supported interpreter, Python
and English-language dependencies, writable directories, model weights, default
Spanish and American English voices, plus either a built Quarian CLI or a
checkout and Cargo ready to build it. It never displays user text, tokens, or
audio content. Resolve every `MISSING` line before starting LM Studio.

Results, weights, Cargo caches, and logs remain local and are ignored by Git.
WAV files may contain sensitive content; delete them manually when no longer
needed.

## Tests and regression checks

The fast suite is deterministic and does not load weights, Kokoro, or Cargo:

```bash
.conda/bin/python -m compileall -q audio.py common.py config.py diagnose.py errors.py tts.py quarian_filter.py quarian_tts.py mcp_tools.py server.py
.conda/bin/python tests/run_core_checks.py
.conda/bin/python -m pip check
```

It covers MCP startup and the single-tool schema, language and voice validation,
text chunking, WAV format and metrics, filter-error classification, and
intermediate-file cleanup.

After preparing weights, run the CPU integration checks. They create unique
WAVs in `outputs/`; each verifies its header, finite samples, positive peak,
and positive RMS:

```bash
# American English Kokoro and Quarian synthesis (default test language).
.conda/bin/python tests/test_kokoro_synthesis.py
.conda/bin/python tests/test_quarian_synthesis.py
.conda/bin/python tests/test_mcp_quarian_tool.py

# Spanish Kokoro and Quarian synthesis.
.conda/bin/python tests/test_kokoro_synthesis.py --language es --text "Hola desde Kokoro."
.conda/bin/python tests/test_quarian_synthesis.py --language es --voice ef_dora --text "Hola desde el filtro Quarian."
```

Model and filter operations are serialized within the process, and synthesized
text is never logged.

## Listening review and troubleshooting

Headers and signal metrics prove technical integrity, not perceived quality.
Listen to a short sample after changing versions, voices, languages, or local
parameters. Check intelligibility, missing segments, saturation or clipping,
and the expected Quarian effect. Open a result with:

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
- If American English fails, confirm that `misaki[en]`, SpaCy, and
  `en_core_web_sm` are installed in `.conda`.
- If Cargo or the checkout is missing, install Rust 1.96+, configure
  `QUARIAN_FILTER_REPOSITORY`, or use `QUARIAN_FILTER_BIN`.
- If the filter exhausts resources or times out, reduce text, close
  memory-heavy processes, and adjust timeouts only as an administrator before
  starting the server.
- If LM Studio does not discover the tool, check the paths in
  `lmstudio-mcp.json.example`, reload MCP, and confirm the diagnostic is
  `READY`.

`server.py` is an MCP stdio server. Running it directly waits for protocol
messages and does not open a terminal user interface.
