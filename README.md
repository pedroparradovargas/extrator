# extrator — Laboratorio de ingeniería inversa

Herramientas didácticas para "abrir por dentro" cosas binarias:

1. **`mini_decompiler.py`** — analiza y desensambla ejecutables PE (`.exe`).
2. **`inspector_modelos.py`** — descarga modelos de IA de HuggingFace y abre su
   estructura interna (arquitectura, capas y tensores). Ver
   [Inspector de modelos de IA](#inspector-de-modelos-de-ia).
3. **`visor.py`** — una **vista web** que muestra la estructura de todo el código
   del repositorio y permite **cargar un modelo** para inspeccionarlo. Ver
   [Visor web](#visor-web).

## Visor web

Una sola página que reúne todo:

```bash
python visor.py                 # abre en http://localhost:8000
python visor.py --port 9000
```

- **Panel izquierdo:** estructura de **todo el código** del repo (archivos, clases
  y funciones), generada automáticamente con `ast`.
- **Panel derecho:** formulario **"Cargar modelo"** — sube un `.safetensors`/`.gguf`,
  o escribe la ruta de una carpeta local o un `repo_id` de HuggingFace, y muestra
  su arquitectura y todos sus tensores.

Solo usa la **librería estándar** de Python (no necesita Flask) y funciona offline
para archivos/carpetas locales.

---

## mini_decompiler — analizador / desensamblador de ejecutables PE (.exe)

Laboratorio didáctico de ingeniería inversa de ejecutables PE de Windows.
Toma un `.exe`, analiza su estructura, traduce su código máquina a ensamblador
y dibuja su grafo de flujo de control (CFG).

> **No es un decompilador.** No reconstruye código fuente C ni pseudocódigo de
> alto nivel. Es un **desensamblador/analizador**: muestra la estructura del
> binario y su código en ensamblador x86/x64.

## Fases

| Fase | Qué hace |
|------|----------|
| 0 | **Identifica con qué se hizo el .exe** y recomienda la herramienta para ver su fuente |
| 1 | Estructura PE: cabeceras, secciones e importaciones (APIs externas) |
| 2 | Desensamblado del código máquina a ensamblador con Capstone |
| 3 | Detección de bloques básicos (líderes del grafo de flujo) |
| 4 | Construcción del grafo de flujo (CFG) y exportación a Graphviz DOT |

## Instalación

```bash
pip install -r requirements.txt          # uso normal (pefile, capstone)
pip install -r requirements-dev.txt      # además, pytest para las pruebas
```

## Uso

```bash
# Análisis básico por pantalla
python mini_decompiler.py binario.exe

# Guardar el informe y exportar el grafo de flujo
python mini_decompiler.py binario.exe -o informe.txt --cfg flujo.dot

# Limitar el número de instrucciones desensambladas
python mini_decompiler.py binario.exe -m 200
```

### Opciones

| Opción | Descripción |
|--------|-------------|
| `-o, --output ARCHIVO` | Guarda el informe de texto en un archivo |
| `-m, --max-inst N` | Máximo de instrucciones a desensamblar (def. 120) |
| `--cfg ARCHIVO.dot` | Exporta el grafo de flujo en formato Graphviz DOT |

### Renderizar el grafo de flujo

Si tienes Graphviz instalado:

```bash
dot -Tpng flujo.dot -o flujo.png
```

## Pruebas

```bash
pip install -r requirements-dev.txt
pytest -q
```

Las pruebas no necesitan un `.exe` externo ni un compilador: `tests/conftest.py`
construye un PE de 32 bits mínimo y válido en memoria con `struct`.

## ¿Quiero ver el código fuente de un .exe?

El **código fuente original casi nunca se recupera tal cual** de un `.exe`: la
compilación pierde nombres, comentarios y estructura. Lo que se obtiene depende
del lenguaje con que se creó. La **Fase 0** detecta el tipo y te dice qué usar:

| Tipo de `.exe` | ¿Se recupera el fuente? | Herramienta |
|---|---|---|
| **.NET (C# / VB.NET)** | Casi idéntico al original | ILSpy, dnSpy |
| **AutoIt** | Casi entero | Exe2Aut, myAut2Exe |
| **Python** (PyInstaller/py2exe) | El `.py` o muy parecido | pyinstxtractor + decompyle3 |
| **Visual Basic 6** | Parcial | VB Decompiler |
| **Go / Rust / Delphi** | Parcial (solo pseudocódigo) | Ghidra, IDA, IDR |
| **C / C++ nativo** | No; solo **pseudocódigo** | Ghidra (gratis), IDA, RetDec |
| **UPX (empaquetado)** | Hay que desempaquetar antes | `upx -d binario.exe` |

Ejecuta `python mini_decompiler.py binario.exe` y mira la sección
*IDENTIFICACIÓN DEL BINARIO* al principio del informe.

## Aviso de seguridad

Empieza con un `.exe` que **tú mismo compiles** (por ejemplo un "hola mundo" en C
con MinGW o MSVC) para poder verificar que la salida coincide con lo que esperas.
**No analices binarios desconocidos fuera de una máquina virtual aislada.**

---

## Inspector de modelos de IA

`inspector_modelos.py` **descarga** un modelo libre de HuggingFace, lo **guarda**
en disco y **abre su estructura interna** para ver cómo es por dentro.

> A un modelo no se le "descompila" (no es un ejecutable). Pero su anatomía sí es
> legible: el formato **`.safetensors`** guarda en una cabecera JSON todos los
> tensores (capas) con su nombre, forma y tipo de dato — se lee **sin cargar los
> pesos en memoria**. El `config.json` describe la arquitectura.

### Uso

```bash
pip install -r requirements.txt        # incluye huggingface_hub

# Descargar + abrir un modelo pequeño
python inspector_modelos.py gpt2

# Solo la arquitectura, sin bajar los pesos grandes (rápido)
python inspector_modelos.py meta-llama/Llama-3.2-1B --solo-config

# Inspeccionar un modelo ya descargado
python inspector_modelos.py ./modelos/gpt2 --solo-local

# Exportar la estructura a JSON
python inspector_modelos.py gpt2 --json estructura.json
```

Muestra: arquitectura (tipo, capas, cabezas, vocabulario…), nº de parámetros,
tamaño de los pesos, y la lista de tensores con sus formas. Detecta también
`.gguf` (llama.cpp), `.bin` (PyTorch) y `.onnx`.

### Formatos soportados

| Formato | Qué hace el inspector |
|---|---|
| `.safetensors` | Lee toda la estructura (tensores, formas, tipos) — formato principal |
| `config.json` | Extrae la arquitectura del modelo |
| `.gguf` | Lee la cabecera básica (versión, nº de tensores) |
| `.bin` / `.onnx` | Los detecta y sugiere la herramienta para abrirlos |

> **Nota de red:** descargar requiere acceso a `huggingface.co`. En un entorno con
> la red restringida, usa `--solo-local` sobre una carpeta ya descargada, o ajusta
> la política de red de la sesión.

---

## Estructura del proyecto

```
extrator/
├── README.md
├── requirements.txt          # pefile, capstone, huggingface_hub
├── requirements-dev.txt      # pytest
├── mini_decompiler.py        # analizador/desensamblador PE + CLI
├── inspector_modelos.py      # descarga e inspecciona modelos de IA + CLI
├── visor.py                  # vista web del repo + cargador de modelos
└── tests/
    ├── conftest.py           # genera un PE mínimo de prueba
    ├── test_pe.py            # PE: Fase 1
    ├── test_disasm.py        # PE: Fase 2
    ├── test_cfg.py           # PE: Fases 3 y 4
    ├── test_detect.py        # PE: Fase 0 (identificación)
    ├── test_inspector.py     # Inspector de modelos de IA
    └── test_visor.py         # Visor web
```
