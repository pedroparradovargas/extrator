"""Pruebas del inspector de modelos: lectura de estructura .safetensors.

No requieren red: se construye un .safetensors mínimo a mano (cabecera JSON
de 8 bytes de longitud + cabecera + datos), igual que el formato real.
"""

import json
import struct

from inspector_modelos import (
    leer_safetensors_header, resumir_tensores, leer_config,
    inspeccionar_directorio, leer_gguf_basico, _params_tensor,
)


def _escribir_safetensors(ruta, tensores, metadata=None):
    """Crea un .safetensors válido con tensores de ceros."""
    cabecera = {}
    offset = 0
    for nombre, (dtype, shape, dsize) in tensores.items():
        n = _params_tensor(shape) * dsize
        cabecera[nombre] = {"dtype": dtype, "shape": shape,
                            "data_offsets": [offset, offset + n]}
        offset += n
    if metadata:
        cabecera["__metadata__"] = metadata
    blob = json.dumps(cabecera).encode("utf-8")
    with open(ruta, "wb") as f:
        f.write(struct.pack("<Q", len(blob)))
        f.write(blob)
        f.write(b"\x00" * offset)


def test_leer_header(tmp_path):
    ruta = tmp_path / "model.safetensors"
    _escribir_safetensors(ruta, {
        "embed.weight": ("F32", [10, 4], 4),
        "lin.weight": ("F16", [4, 4], 2),
    }, metadata={"format": "pt"})

    meta, tensores = leer_safetensors_header(str(ruta))
    assert meta == {"format": "pt"}
    assert set(tensores) == {"embed.weight", "lin.weight"}
    assert tensores["embed.weight"]["shape"] == [10, 4]
    assert tensores["lin.weight"]["dtype"] == "F16"


def test_resumir():
    tensores = {
        "a": {"dtype": "F32", "shape": [10, 4]},   # 40 params * 4 = 160 B
        "b": {"dtype": "F16", "shape": [4, 4]},     # 16 params * 2 = 32 B
    }
    res = resumir_tensores(tensores)
    assert res["num_tensores"] == 2
    assert res["total_params"] == 56
    assert res["total_bytes"] == 192
    assert res["por_dtype"] == {"F32": 1, "F16": 1}


def test_inspeccionar_directorio(tmp_path):
    # config.json
    (tmp_path / "config.json").write_text(json.dumps({
        "model_type": "bert",
        "hidden_size": 4,
        "num_hidden_layers": 2,
    }))
    # un .safetensors con tensores de dos "capas"
    _escribir_safetensors(tmp_path / "model.safetensors", {
        "encoder.layer.0.weight": ("F32", [4, 4], 4),
        "encoder.layer.1.weight": ("F32", [4, 4], 4),
        "embeddings.weight": ("F32", [10, 4], 4),
    })

    estado = inspeccionar_directorio(str(tmp_path))
    assert estado["config"]["model_type"] == "bert"
    assert estado["resumen"]["num_tensores"] == 3
    assert estado["resumen"]["total_params"] == 4 * 4 + 4 * 4 + 10 * 4
    assert len(estado["safetensors"]) == 1


def test_config_inexistente(tmp_path):
    assert leer_config(str(tmp_path)) == {}


def test_gguf_basico(tmp_path):
    ruta = tmp_path / "modelo.gguf"
    with open(ruta, "wb") as f:
        f.write(b"GGUF")
        f.write(struct.pack("<IQQ", 3, 291, 25))   # version 3, 291 tensores, 25 kv
    info = leer_gguf_basico(str(ruta))
    assert info == {"version": 3, "num_tensores": 291, "num_metadata": 25}


def test_gguf_magic_invalido(tmp_path):
    ruta = tmp_path / "no.gguf"
    ruta.write_bytes(b"XXXX" + b"\x00" * 20)
    assert leer_gguf_basico(str(ruta)) is None
