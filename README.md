# Quarian TTS Local MCP

Servidor MCP local y modular para generar un WAV con este flujo final:

```text
texto → Kokoro TTS (CPU) → quarian-voice-filter-cli (CPU) → WAV
```

El repositorio está deliberadamente limitado a voz quariana. No contiene ni
contendrá OCR, traducción, STT, Ollama, imágenes ni estado de resultados de esos
flujos.

## Estado actual: fase 3 — adaptador seguro del filtro Quarian

El armazón MCP sigue sin registrar herramientas. El núcleo local genera Kokoro
bajo demanda y ahora encadena la CLI Rust `quarian-voice-filter-cli` sobre su
WAV PCM16 mono de 24 kHz. La única herramienta MCP llegará en la fase 4.

```text
quarian-tts-local-mcp/
├── config.py                # Rutas, límites y caché local de Kokoro
├── common.py                # Logging, métricas y bloqueo del modelo
├── errors.py                # Errores seguros y tipados
├── audio.py                 # Nombres y validación de WAV PCM16/24 kHz
├── tts.py                   # Síntesis Kokoro local y división por oraciones
├── quarian_filter.py        # Build y ejecución segura de la CLI Rust
├── quarian_tts.py           # Orquestación Kokoro → filtro y limpieza temporal
├── server.py                # Punto de entrada MCP por stdio; sin herramientas aún
├── models/                  # Pesos locales futuros; ignorados por Git
├── outputs/                 # WAV futuros; ignorados por Git
├── logs/                    # server.log local; ignorado por Git
├── tests/
├── pyproject.toml
└── requirements.txt
```

Todos los módulos Python viven en la raíz del repositorio; no existe ni se
creará un directorio `src/`.

## Entorno local

Se requiere Python 3.12 o 3.13. Cree un entorno aislado dentro del proyecto:

```bash
cd /home/juan/Dev/commander-spaceman/quarian-tts-local-mcp
/home/juan/.miniconda3/bin/conda create --prefix "$PWD/.conda" python=3.12 -y
"$PWD/.conda/bin/python" -m pip install --upgrade pip
"$PWD/.conda/bin/python" -m pip install -r requirements.txt
"$PWD/.conda/bin/python" -m pip install --no-deps -e .
"$PWD/.conda/bin/python" -m pip check
```

El archivo fija PyTorch CPU, Kokoro, NumPy, SoundFile y MCP. No instala CUDA ni
ninguna dependencia de OCR, STT, traducción u Ollama.

En Ubuntu también se necesitan las bibliotecas del sistema usadas por Kokoro y
SoundFile:

```bash
sudo apt install espeak-ng libsndfile1
```

## Pesos locales de Kokoro

La síntesis sólo lee pesos locales y no descarga modelos durante una llamada.
Debe existir esta estructura:

```text
models/kokoro/source/
├── config.json
├── kokoro-v1_0.pth
└── voices/
    ├── ef_dora.pt
    ├── em_alex.pt          # opcional, si se quiere usar
    └── em_santa.pt         # opcional, si se quiere usar
```

Para reutilizar una copia existente sin duplicarla:

```bash
mkdir -p models/kokoro
ln -s /home/juan/ai-models/Kokoro-82M models/kokoro/source
```

Como alternativa, descargue los pesos públicos una vez fuera de una llamada MCP:

```bash
.conda/bin/hf download hexgrad/Kokoro-82M --local-dir models/kokoro/source
```

`models/` está ignorado por Git. Las voces aceptadas son `ef_dora`, `em_alex` y
`em_santa`; una voz aceptada pero ausente en disco falla de forma explícita.

## Rutas locales

Por defecto, el directorio raíz es este checkout. Un administrador puede mover
la raíz de datos estableciendo `QUARIAN_TTS_ROOT` antes de iniciar el proceso.
Las rutas derivadas son:

- `models/`: futuros pesos locales;
- `outputs/`: WAV finales e intermedios temporales de fases posteriores;
- `logs/server.log`: registro rotativo que no usa stdout.

Los parámetros MCP no pueden cambiar estas rutas.

## Filtro Quarian local

El adaptador lee la CLI documentada del checkout local:

```text
/home/juan/Dev/commander-spaceman/quarian-voice-filter
```

Requiere Rust/Cargo 1.96 o posterior. En la primera ejecución, compila sólo el
paquete `quarian-voice-filter-cli`, con un trabajo de Cargo. Las descargas y los
artefactos quedan aislados en `.quarian-cargo/` y `.quarian-filter-build/`;
ninguno se versiona ni modifica el checkout externo.

Un administrador puede sustituir esas ubicaciones, antes de iniciar el proceso:

- `QUARIAN_FILTER_REPOSITORY`: checkout local alternativo;
- `QUARIAN_FILTER_BIN`: ejecutable ya compilado; evita la compilación;
- `QUARIAN_FILTER_TIMEOUT_SECONDS`: límite de ejecución, por defecto `120`;
- `QUARIAN_FILTER_BUILD_TIMEOUT_SECONDS`: límite de compilación, por defecto
  `600`.

No son parámetros MCP. La entrada y salida se validan antes y después de llamar
la CLI; ambas deben ser WAV PCM16, mono y de 24 kHz. Cada ejecución usa un
nombre nuevo, nunca sobrescribe resultados, bloquea llamadas concurrentes al
filtro y elimina el WAV Kokoro intermedio, incluso ante errores. Los logs sólo
incluyen metadatos, tiempos, ruta y tamaño de stderr; no incluyen el texto ni
el contenido de stderr.

## Verificación de las fases 2 y 3

Las pruebas de núcleo no cargan pesos ni sintetizan audio:

```bash
.conda/bin/python -m compileall -q audio.py common.py config.py errors.py tts.py quarian_filter.py quarian_tts.py server.py
.conda/bin/python tests/test_bootstrap.py
.conda/bin/python tests/test_tts_core.py
.conda/bin/python tests/test_quarian_filter_core.py
```

Tras preparar los pesos, ejecute las comprobaciones manuales de CPU. Crean un
WAV único en `outputs/` y verifican sus cabeceras:

```bash
# Sólo Kokoro.
.conda/bin/python tests/test_kokoro_synthesis.py

# Kokoro seguido del filtro Quarian; también comprueba que los bytes cambiaron.
.conda/bin/python tests/test_quarian_synthesis.py
```

Los límites actuales son 12.000 caracteres, velocidad entre `0.7` y `1.3`, y
fragmentos de hasta 800 caracteres separados preferentemente por oraciones.
Las operaciones sobre el modelo se serializan dentro del proceso y nunca se
registra el texto sintetizado.

`server.py` es un servidor MCP por `stdio`, por lo que al ejecutarlo
directamente esperará mensajes del protocolo; todavía anuncia un catálogo vacío
de herramientas.

## Próxima fase

La fase 4 expondrá una sola herramienta MCP:
`generate_quarian_audio(text, voice, speed)`. Será una envoltura de la
orquestación ya validada, devolverá la ruta absoluta y metadatos seguros, y no
incorporará herramientas de OCR, traducción o STT.
