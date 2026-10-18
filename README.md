# Quarian TTS Local MCP

Servidor MCP local y modular para generar un WAV con este flujo final:

```text
texto → Kokoro TTS (CPU) → quarian-voice-filter-cli (CPU) → WAV
```

El repositorio está deliberadamente limitado a voz quariana. No contiene ni
contendrá OCR, traducción, STT, Ollama, imágenes ni estado de resultados de esos
flujos.

## Estado actual: fase 2 — núcleo modular de Kokoro TTS

El armazón MCP sigue sin registrar herramientas. Esta fase añade exclusivamente
el núcleo local de síntesis: valida texto/voz/velocidad, carga Kokoro bajo
demanda desde pesos locales y escribe WAV PCM16 mono de 24 kHz. El filtro
Quarian aún no se ejecuta.

```text
quarian-tts-local-mcp/
├── config.py                # Rutas, límites y caché local de Kokoro
├── common.py                # Logging, métricas y bloqueo del modelo
├── errors.py                # Errores seguros y tipados
├── audio.py                 # Nombres y validación de WAV PCM16/24 kHz
├── tts.py                   # Síntesis Kokoro local y división por oraciones
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

## Verificación de la fase 2

Las pruebas de núcleo no cargan pesos ni sintetizan audio:

```bash
.conda/bin/python -m compileall -q audio.py common.py config.py errors.py tts.py server.py
.conda/bin/python tests/test_bootstrap.py
.conda/bin/python tests/test_tts_core.py
```

Tras preparar los pesos, ejecute la comprobación manual de CPU. Crea un WAV
único en `outputs/` y verifica su cabecera:

```bash
.conda/bin/python tests/test_kokoro_synthesis.py
```

Los límites actuales son 12.000 caracteres, velocidad entre `0.7` y `1.3`, y
fragmentos de hasta 800 caracteres separados preferentemente por oraciones.
Las operaciones sobre el modelo se serializan dentro del proceso y nunca se
registra el texto sintetizado.

`server.py` es un servidor MCP por `stdio`, por lo que al ejecutarlo
directamente esperará mensajes del protocolo; todavía anuncia un catálogo vacío
de herramientas.

## Próxima fase

La fase 3 añadirá el adaptador seguro de la CLI Rust
`quarian-voice-filter-cli`: compilación local perezosa, timeout, validación de
entrada/salida y limpieza del WAV intermedio. La única herramienta MCP llegará
en la fase 4.
