# extrator — Mini-analizador / desensamblador de ejecutables PE (.exe)

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

## Estructura del proyecto

```
extrator/
├── README.md
├── requirements.txt          # pefile, capstone
├── requirements-dev.txt      # pytest
├── mini_decompiler.py        # módulo principal + CLI
└── tests/
    ├── conftest.py           # genera un PE mínimo de prueba
    ├── test_pe.py            # Fase 1
    ├── test_disasm.py        # Fase 2
    └── test_cfg.py           # Fases 3 y 4
```
