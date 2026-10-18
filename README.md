# Quarian TTS Local MCP

Servidor MCP local y modular para generar un WAV con este flujo final:

```text
texto → Kokoro TTS (CPU) → quarian-voice-filter-cli (CPU) → WAV
```

El repositorio está deliberadamente limitado a voz quariana. No contiene ni
contendrá OCR, traducción, STT, Ollama, imágenes ni estado de resultados de esos
flujos.

## Estado actual: fase 1 — base aislada

Esta fase deja listo el armazón operativo, sin registrar todavía herramientas
MCP ni cargar modelos:

```text
quarian-tts-local-mcp/
├── config.py                # Rutas locales administradas, sin entradas MCP
├── common.py                # Logging rotativo sin stdout
├── server.py                # Punto de entrada MCP por stdio
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

La fase 1 instala sólo `mcp`. Kokoro, PyTorch, `soundfile` y las dependencias de
la CLI se incorporarán cuando se implemente la fase 2 y no antes.

## Rutas locales

Por defecto, el directorio raíz es este checkout. Un administrador puede mover
la raíz de datos estableciendo `QUARIAN_TTS_ROOT` antes de iniciar el proceso.
Las rutas derivadas son:

- `models/`: futuros pesos locales;
- `outputs/`: WAV finales e intermedios temporales de fases posteriores;
- `logs/server.log`: registro rotativo que no usa stdout.

Los parámetros MCP no pueden cambiar estas rutas.

## Verificación de la fase 1

```bash
.conda/bin/python -m compileall -q config.py common.py server.py
.conda/bin/python tests/test_bootstrap.py
```

La segunda comprobación negocia el servidor en memoria y confirma que su
catálogo de herramientas está vacío en esta fase. `server.py` es un servidor
MCP por `stdio`, por lo que al ejecutarlo directamente esperará mensajes del
protocolo; no abre una interfaz de terminal.

## Próxima fase

La fase 2 añadirá los módulos de síntesis Kokoro, validación de parámetros y
creación de WAV PCM16 mono a 24 kHz. El adaptador del filtro Rust y la única
herramienta MCP llegarán en las fases 3 y 4 respectivamente.
