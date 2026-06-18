#!/usr/bin/env python3
"""
inspector_modelos.py
Descarga modelos de IA libres desde HuggingFace y "abre" su estructura interna.

No se "descompila" un modelo (no es un ejecutable), pero sí se puede inspeccionar
su anatomía: la arquitectura (config.json), y todos sus tensores/capas —nombre,
forma (shape), tipo de dato y nº de parámetros— leyendo la cabecera del formato
.safetensors SIN cargar los pesos en memoria.

  Paso 1: DESCARGAR el modelo desde HuggingFace y GUARDARLO en disco
  Paso 2: ABRIR e inspeccionar su estructura (arquitectura + tensores)

Instalación:
    pip install -r requirements.txt        (incluye huggingface_hub)

Uso:
    # Descargar + inspeccionar (modelos pequeños como gpt2 o all-MiniLM-L6-v2)
    python inspector_modelos.py gpt2

    # Solo la arquitectura, sin bajar los pesos grandes (rápido)
    python inspector_modelos.py meta-llama/Llama-3.2-1B --solo-config

    # Inspeccionar un modelo ya descargado en una carpeta local
    python inspector_modelos.py ./modelos/gpt2 --solo-local

    # Guardar el informe en JSON
    python inspector_modelos.py gpt2 --json estructura.json
"""

import argparse
import json
import os
import struct
import sys


# Tamaño en bytes de cada tipo de dato de safetensors.
DTYPE_BYTES = {
    "F64": 8, "I64": 8, "U64": 8,
    "F32": 4, "I32": 4, "U32": 4,
    "F16": 2, "BF16": 2, "I16": 2, "U16": 2,
    "F8_E4M3": 1, "F8_E5M2": 1, "I8": 1, "U8": 1, "BOOL": 1,
}

ANCHO = 70


def _titulo(texto):
    return ["=" * ANCHO, f" {texto}", "=" * ANCHO]


def _humano(n):
    """Formatea un nº grande: 1234567 -> '1.23 M'."""
    for unidad, umbral in (("B", 1e9), ("M", 1e6), ("K", 1e3)):
        if abs(n) >= umbral:
            return f"{n / umbral:.2f} {unidad}"
    return str(n)


def _bytes_humano(n):
    for unidad, umbral in (("GB", 1024**3), ("MB", 1024**2), ("KB", 1024)):
        if n >= umbral:
            return f"{n / umbral:.2f} {unidad}"
    return f"{n} B"


# ---------------------------------------------------------------------------
# PASO 1: descarga desde HuggingFace
# ---------------------------------------------------------------------------
def descargar_modelo(repo_id, destino=None, solo_config=False, token=None):
    """Descarga un modelo de HuggingFace y lo guarda en disco.

    Devuelve la ruta local donde quedó guardado. Lanza ValueError con un
    mensaje claro si falta huggingface_hub o si falla la conexión.
    """
    try:
        from huggingface_hub import snapshot_download
    except ImportError:
        raise ValueError(
            "Falta huggingface_hub. Ejecuta: pip install -r requirements.txt"
        )

    if destino is None:
        carpeta = repo_id.replace("/", "__")
        destino = os.path.join("modelos", carpeta)

    # Patrones de archivos a bajar: solo la estructura, o estructura + pesos.
    if solo_config:
        patrones = ["*.json"]                    # config + índice de shards
    else:
        patrones = ["*.json", "*.safetensors", "*.model", "tokenizer*", "*.txt"]

    try:
        ruta = snapshot_download(
            repo_id=repo_id,
            local_dir=destino,
            allow_patterns=patrones,
            token=token,
        )
    except Exception as e:                        # red, repo inexistente, auth...
        raise ValueError(
            f"No se pudo descargar '{repo_id}': {type(e).__name__}: {e}"
        )
    return ruta


# ---------------------------------------------------------------------------
# PASO 2: leer la estructura
# ---------------------------------------------------------------------------
def leer_safetensors_header(ruta):
    """Lee SOLO la cabecera de un .safetensors (no carga los pesos).

    Devuelve (metadata, tensores) donde tensores es un dict
    {nombre: {"dtype": str, "shape": [int...], "data_offsets": [int,int]}}.
    """
    with open(ruta, "rb") as f:
        cabecera_len = struct.unpack("<Q", f.read(8))[0]
        cabecera = json.loads(f.read(cabecera_len))

    metadata = cabecera.pop("__metadata__", {})
    return metadata, cabecera


def _params_tensor(shape):
    total = 1
    for d in shape:
        total *= d
    return total


def resumir_tensores(tensores):
    """Calcula totales a partir del dict de tensores de una cabecera."""
    total_params = 0
    total_bytes = 0
    por_dtype = {}
    for info in tensores.values():
        shape = info.get("shape", [])
        dtype = info.get("dtype", "?")
        params = _params_tensor(shape)
        total_params += params
        total_bytes += params * DTYPE_BYTES.get(dtype, 0)
        por_dtype[dtype] = por_dtype.get(dtype, 0) + 1
    return {
        "num_tensores": len(tensores),
        "total_params": total_params,
        "total_bytes": total_bytes,
        "por_dtype": por_dtype,
    }


def leer_gguf_basico(ruta):
    """Lee la cabecera básica de un .gguf (formato de llama.cpp)."""
    with open(ruta, "rb") as f:
        magic = f.read(4)
        if magic != b"GGUF":
            return None
        version, n_tensores, n_kv = struct.unpack("<IQQ", f.read(20))
    return {"version": version, "num_tensores": n_tensores, "num_metadata": n_kv}


def leer_config(directorio):
    """Carga config.json si existe; devuelve {} si no."""
    ruta = os.path.join(directorio, "config.json")
    if not os.path.isfile(ruta):
        return {}
    try:
        with open(ruta, encoding="utf-8") as f:
            return json.load(f)
    except (OSError, json.JSONDecodeError):
        return {}


def inspeccionar_directorio(directorio):
    """Recorre una carpeta de modelo y agrega toda su estructura.

    Devuelve un dict con: config, archivos por formato, tensores agregados
    de todos los .safetensors, y el resumen global.
    """
    safetensors = []
    otros = {"gguf": [], "bin": [], "onnx": [], "pth": []}
    for raiz, _, archivos in os.walk(directorio):
        for nombre in archivos:
            ruta = os.path.join(raiz, nombre)
            bajo = nombre.lower()
            if bajo.endswith(".safetensors"):
                safetensors.append(ruta)
            elif bajo.endswith(".gguf"):
                otros["gguf"].append(ruta)
            elif bajo.endswith(".bin"):
                otros["bin"].append(ruta)
            elif bajo.endswith(".onnx"):
                otros["onnx"].append(ruta)
            elif bajo.endswith((".pt", ".pth")):
                otros["pth"].append(ruta)

    tensores_global = {}
    metadata_global = {}
    for ruta in sorted(safetensors):
        try:
            meta, tensores = leer_safetensors_header(ruta)
        except (OSError, struct.error, json.JSONDecodeError):
            continue
        metadata_global.update(meta)
        rel = os.path.relpath(ruta, directorio)
        for nombre, info in tensores.items():
            info = dict(info)
            info["_archivo"] = rel
            tensores_global[nombre] = info

    return {
        "config": leer_config(directorio),
        "safetensors": sorted(safetensors),
        "otros": otros,
        "metadata": metadata_global,
        "tensores": tensores_global,
        "resumen": resumir_tensores(tensores_global),
    }


# ---------------------------------------------------------------------------
# Presentación
# ---------------------------------------------------------------------------
# Claves de config.json que describen la arquitectura, con etiqueta legible.
CLAVES_ARQ = [
    ("model_type", "Tipo de modelo"),
    ("architectures", "Arquitectura(s)"),
    ("hidden_size", "Tamaño oculto (hidden_size)"),
    ("intermediate_size", "Tamaño intermedio (FFN)"),
    ("num_hidden_layers", "Nº de capas"),
    ("num_attention_heads", "Nº de cabezas de atención"),
    ("num_key_value_heads", "Nº de cabezas KV"),
    ("vocab_size", "Tamaño del vocabulario"),
    ("max_position_embeddings", "Posiciones máximas (contexto)"),
    ("torch_dtype", "Tipo de dato (torch_dtype)"),
]


def imprimir_arquitectura(config):
    lineas = _titulo("ARQUITECTURA (config.json)")
    if not config:
        lineas.append("  (sin config.json)")
        return lineas
    for clave, etiqueta in CLAVES_ARQ:
        if clave in config:
            lineas.append(f"  {etiqueta:<32}: {config[clave]}")
    return lineas


def _agrupar_por_capa(tensores):
    """Agrupa tensores por su prefijo de capa para ver el patrón repetido.

    p.ej. 'model.layers.0.', 'model.layers.1.' ... -> cuenta de capas.
    """
    import re
    capas = set()
    prefijos = {}
    for nombre in tensores:
        m = re.search(r"\.(\d+)\.", nombre)
        if m:
            capas.add(int(m.group(1)))
        # prefijo hasta el primer número, para contar tipos de módulo
        pref = re.sub(r"\.\d+\.", ".N.", nombre)
        prefijos[pref] = prefijos.get(pref, 0) + 1
    return capas, prefijos


def imprimir_tensores(estado, max_tensores=40):
    res = estado["resumen"]
    lineas = [""] + _titulo("TENSORES / CAPAS (.safetensors)")
    if res["num_tensores"] == 0:
        lineas.append("  (no se encontraron .safetensors)")
        # informar de otros formatos detectados
        for fmt, rutas in estado["otros"].items():
            if rutas:
                lineas.append(f"  Detectados {len(rutas)} archivo(s) .{fmt}")
        return lineas

    lineas.append(f"  Archivos .safetensors : {len(estado['safetensors'])}")
    lineas.append(f"  Nº de tensores        : {res['num_tensores']}")
    lineas.append(f"  Parámetros totales    : {_humano(res['total_params'])}"
                  f"  ({res['total_params']:,})")
    lineas.append(f"  Tamaño de los pesos   : {_bytes_humano(res['total_bytes'])}")
    lineas.append(f"  Tipos de dato         : "
                  + ", ".join(f"{k} x{v}" for k, v in res["por_dtype"].items()))

    capas, prefijos = _agrupar_por_capa(estado["tensores"])
    if capas:
        lineas.append(f"  Capas repetidas       : {len(capas)} "
                      f"(índices {min(capas)}..{max(capas)})")

    lineas.append("")
    lineas.append(f"  Primeros tensores (de {res['num_tensores']}):")
    lineas.append(f"    {'NOMBRE':<48}{'DTYPE':<8}SHAPE")
    for i, (nombre, info) in enumerate(estado["tensores"].items()):
        if i >= max_tensores:
            lineas.append(f"    ... ({res['num_tensores'] - max_tensores} más)")
            break
        shape = "x".join(str(d) for d in info.get("shape", [])) or "escalar"
        lineas.append(f"    {nombre:<48}{info.get('dtype','?'):<8}{shape}")
    return lineas


def imprimir_otros_formatos(estado):
    lineas = []
    otros = estado["otros"]
    if any(otros.values()):
        lineas += [""] + _titulo("OTROS FORMATOS DETECTADOS")
        for ruta in otros["gguf"]:
            info = leer_gguf_basico(ruta)
            extra = (f" — v{info['version']}, {info['num_tensores']} tensores"
                     if info else "")
            lineas.append(f"  GGUF (llama.cpp): {os.path.basename(ruta)}{extra}")
        for ruta in otros["bin"]:
            lineas.append(f"  PyTorch .bin (pickle): {os.path.basename(ruta)} "
                          f"— inspecciónalo con torch o conviértelo a safetensors")
        for ruta in otros["onnx"]:
            lineas.append(f"  ONNX: {os.path.basename(ruta)} — ábrelo con Netron")
        for ruta in otros["pth"]:
            lineas.append(f"  PyTorch checkpoint: {os.path.basename(ruta)}")
    return lineas


def generar_informe(estado, max_tensores=40):
    lineas = []
    lineas += imprimir_arquitectura(estado["config"])
    lineas += imprimir_tensores(estado, max_tensores)
    lineas += imprimir_otros_formatos(estado)
    return "\n".join(lineas)


def estado_para_json(estado):
    """Versión serializable (sin objetos pesados) del estado."""
    return {
        "config": estado["config"],
        "metadata": estado["metadata"],
        "resumen": estado["resumen"],
        "tensores": estado["tensores"],
        "safetensors": [os.path.basename(p) for p in estado["safetensors"]],
    }


# ---------------------------------------------------------------------------
# CLI
# ---------------------------------------------------------------------------
def parse_args(argv=None):
    p = argparse.ArgumentParser(
        description="Descarga un modelo de HuggingFace y abre su estructura interna.",
    )
    p.add_argument("modelo",
                   help="repo_id de HuggingFace (p.ej. 'gpt2') o ruta local")
    p.add_argument("--dir", metavar="CARPETA",
                   help="carpeta donde guardar/leer el modelo")
    p.add_argument("--solo-config", action="store_true",
                   help="bajar solo la arquitectura (sin los pesos grandes)")
    p.add_argument("--solo-local", action="store_true",
                   help="no descargar: inspeccionar una carpeta ya existente")
    p.add_argument("--max-tensores", type=int, default=40, metavar="N",
                   help="cuántos tensores listar (def. 40)")
    p.add_argument("--json", metavar="ARCHIVO",
                   help="guardar la estructura en formato JSON")
    p.add_argument("--token", metavar="TOKEN",
                   help="token de HuggingFace para modelos con acceso restringido")
    return p.parse_args(argv)


def main(argv=None):
    args = parse_args(argv)

    # ¿Es ya una carpeta local, o hay que descargar?
    if args.solo_local or os.path.isdir(args.modelo):
        directorio = args.modelo if os.path.isdir(args.modelo) else args.dir
        if not directorio or not os.path.isdir(directorio):
            print(f"Error: no existe la carpeta '{directorio}'", file=sys.stderr)
            return 1
        print(f"[*] Inspeccionando carpeta local: {directorio}")
    else:
        print(f"[*] Descargando '{args.modelo}' desde HuggingFace...")
        try:
            directorio = descargar_modelo(
                args.modelo, destino=args.dir,
                solo_config=args.solo_config, token=args.token,
            )
        except ValueError as e:
            print(f"Error: {e}", file=sys.stderr)
            return 1
        print(f"[+] Guardado en: {directorio}")

    estado = inspeccionar_directorio(directorio)
    informe = generar_informe(estado, args.max_tensores)
    print()
    print(informe)

    if args.json:
        try:
            with open(args.json, "w", encoding="utf-8") as f:
                json.dump(estado_para_json(estado), f, indent=2, ensure_ascii=False)
            print(f"\n[+] Estructura guardada en JSON: {args.json}")
        except OSError as e:
            print(f"Error al escribir JSON: {e}", file=sys.stderr)
            return 1
    return 0


if __name__ == "__main__":
    sys.exit(main())
