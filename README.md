# Quarian TTS Local MCP

Servidor MCP local y modular para generar un WAV con este flujo final:

```text
texto → Kokoro TTS (CPU) → quarian-voice-filter-cli (CPU) → WAV
```

El repositorio está deliberadamente limitado a voz quariana. No contiene ni
contendrá OCR, traducción, STT, Ollama, imágenes ni estado de resultados de esos
flujos.

## Estado actual: fase 5 — pruebas, operación y documentación

El servidor MCP por `stdio` expone exactamente una herramienta. Genera Kokoro
bajo demanda y encadena la CLI Rust `quarian-voice-filter-cli` sobre su WAV
PCM16 mono de 24 kHz. La instalación incluye comprobaciones de regresión sin
modelos, diagnósticos locales y pruebas de integración con métricas de señal.
No existen herramientas de OCR, traducción, STT ni lectura de estado.

```text
quarian-tts-local-mcp/
├── config.py                # Rutas, límites y caché local de Kokoro
├── common.py                # Logging, métricas y bloqueo del modelo
├── errors.py                # Errores seguros y tipados
├── audio.py                 # Nombres, validación y métricas PCM16/24 kHz
├── tts.py                   # Síntesis Kokoro local y división por oraciones
├── quarian_filter.py        # Build y ejecución segura de la CLI Rust
├── quarian_tts.py           # Orquestación Kokoro → filtro y limpieza temporal
├── mcp_tools.py             # Adaptador MCP seguro para la única herramienta
├── server.py                # Punto de entrada MCP por stdio y registro de herramienta
├── diagnose.py              # Diagnóstico offline de requisitos locales
├── lmstudio-mcp.json.example
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

## Herramienta MCP

| Herramienta | Parámetros | Resultado |
|---|---|---|
| `generate_quarian_audio` | `text` obligatorio; `voice="ef_dora"`; `speed=1.0` | Nuevo WAV Quarian absoluto en `outputs/` |

`text` admite hasta 12.000 caracteres. `voice` debe ser `ef_dora`, `em_alex` o
`em_santa` y existir localmente. `speed` está entre `0.7` y `1.3`. La respuesta
incluye ruta, duración, frecuencia y voz, pero nunca repite el texto enviado.
Los errores de entrada, pesos, filtro, compilación y timeout se devuelven con
mensajes seguros.

## LM Studio

No sobrescriba su configuración completa. Añada o reemplace sólo la entrada
`quarian-tts-local` de [`lmstudio-mcp.json.example`](lmstudio-mcp.json.example)
en su archivo MCP de LM Studio. Tras recargar MCP debe aparecer una sola
herramienta: `generate_quarian_audio`.

## Diagnóstico operativo

Antes de conectar LM Studio, compruebe requisitos sin cargar Kokoro, compilar
Rust ni generar audio:

```bash
.conda/bin/python diagnose.py
# Después de instalar el proyecto de forma editable:
quarian-tts-diagnose
```

El informe termina en `READY` sólo si encuentra el intérprete compatible,
dependencias Python, directorios escribibles, pesos y voz local, y una CLI
Quarian ya compilada **o** un checkout y Cargo listos para compilar. No muestra
texto de usuario, tokens ni contenido de audio. Corrija cualquier línea
`MISSING` antes de iniciar LM Studio.

Los resultados, pesos, cachés de Cargo y logs permanecen locales e ignorados
por Git. Los WAV pueden contener contenido sensible: elimínelos manualmente
cuando ya no sean necesarios.

## Pruebas y regresión

La batería rápida es determinista y no carga pesos, Kokoro ni Cargo:

```bash
.conda/bin/python -m compileall -q audio.py common.py config.py diagnose.py errors.py tts.py quarian_filter.py quarian_tts.py mcp_tools.py server.py
.conda/bin/python tests/run_core_checks.py
.conda/bin/python -m pip check
```

Incluye arranque MCP, esquema de la única herramienta, límites de entrada,
división de texto, formato y métricas WAV, clasificación de fallos del filtro y
limpieza del intermedio. La salida enumera cada prueba y termina con el número
de verificaciones completadas.

Tras preparar los pesos, ejecute las integraciones de CPU. Crean WAVs únicos en
`outputs/`; cada una verifica cabecera, muestras finitas, pico y RMS positivos:

```bash
# Sólo Kokoro.
.conda/bin/python tests/test_kokoro_synthesis.py

# Kokoro seguido del filtro; también comprueba que los bytes cambiaron.
.conda/bin/python tests/test_quarian_synthesis.py

# La misma síntesis, invocada mediante un cliente MCP en memoria.
.conda/bin/python tests/test_mcp_quarian_tool.py
```

Los límites son 12.000 caracteres, velocidad entre `0.7` y `1.3`, y fragmentos
de hasta 800 caracteres separados preferentemente por oraciones. Las
operaciones sobre el modelo y filtro se serializan dentro del proceso y nunca
se registra el texto sintetizado.

## Revisión auditiva y diagnóstico de fallos

Las cabeceras y métricas confirman integridad técnica, no calidad percibida.
Escuche una muestra corta tras cambiar versiones, voz o parámetros locales y
compruebe inteligibilidad, ausencia de cortes, saturación/clipping y el efecto
Quarian esperado. Puede abrir un resultado con:

```bash
xdg-open outputs/quarian_audio_YYYYMMDD_HHMMSS_microseconds_UUID.wav
```

Para investigar una operación, consulte sólo los metadatos locales:

```bash
tail -n 80 logs/server.log
.conda/bin/python diagnose.py
.conda/bin/python -m pip check
```

- Si faltan pesos o una voz, repare `models/kokoro/source/` y ejecute el
diagnóstico otra vez.
- Si falta Cargo/check-out, instale Rust 1.96+, configure
  `QUARIAN_FILTER_REPOSITORY` o use `QUARIAN_FILTER_BIN`.
- Si el filtro agota recursos o vence el timeout, reduzca el texto, cierre
  procesos pesados y ajuste los timeouts sólo como administrador antes de
  iniciar el servidor.
- Si LM Studio no descubre la herramienta, compruebe las rutas de
  `lmstudio-mcp.json.example`, recargue MCP y confirme que el diagnóstico está
  en `READY`.

`server.py` es un servidor MCP por `stdio`, por lo que al ejecutarlo
directamente esperará mensajes del protocolo y no abre una interfaz de terminal.
