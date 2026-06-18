"""Pruebas del visor: estructura de código, multipart y carga de modelo."""

import json
import struct

from visor import estructura_codigo, parse_multipart, cargar_modelo
from inspector_modelos import inspeccionar


def test_estructura_codigo(tmp_path):
    (tmp_path / "ejemplo.py").write_text(
        "def saluda():\n    pass\n\n"
        "class Caja:\n    def abrir(self):\n        pass\n"
    )
    (tmp_path / "datos.txt").write_text("no es python")
    archivos = estructura_codigo(str(tmp_path))

    assert len(archivos) == 1                      # solo el .py
    a = archivos[0]
    assert a["ruta"] == "ejemplo.py"
    nombres = {s["nombre"] for s in a["simbolos"]}
    assert nombres == {"saluda", "Caja"}
    caja = next(s for s in a["simbolos"] if s["nombre"] == "Caja")
    assert caja["tipo"] == "class"
    assert caja["hijos"][0]["nombre"] == "abrir"


def test_estructura_ignora_pycache(tmp_path):
    (tmp_path / "__pycache__").mkdir()
    (tmp_path / "__pycache__" / "x.py").write_text("def y(): pass")
    (tmp_path / "real.py").write_text("def z(): pass")
    rutas = {a["ruta"] for a in estructura_codigo(str(tmp_path))}
    assert rutas == {"real.py"}


def test_parse_multipart_campo_y_archivo():
    b = b"BOUND"
    cuerpo = (
        b"--BOUND\r\n"
        b'Content-Disposition: form-data; name="fuente"\r\n\r\n'
        b"gpt2\r\n"
        b"--BOUND\r\n"
        b'Content-Disposition: form-data; name="archivo"; filename="m.safetensors"\r\n'
        b"Content-Type: application/octet-stream\r\n\r\n"
        b"\x00\x01\x02\r\n"
        b"--BOUND--\r\n"
    )
    campos, archivos = parse_multipart(cuerpo, b)
    assert campos["fuente"] == "gpt2"
    assert archivos["archivo"][0] == "m.safetensors"
    assert archivos["archivo"][1] == b"\x00\x01\x02"


def _safetensors(ruta, tensores):
    cab, off = {}, 0
    for n, (dt, sh, sz) in tensores.items():
        c = 1
        for d in sh:
            c *= d
        cab[n] = {"dtype": dt, "shape": sh, "data_offsets": [off, off + c * sz]}
        off += c * sz
    blob = json.dumps(cab).encode()
    with open(ruta, "wb") as f:
        f.write(struct.pack("<Q", len(blob)))
        f.write(blob)
        f.write(b"\x00" * off)


def test_cargar_modelo_archivo_subido(tmp_path):
    ruta = tmp_path / "m.safetensors"
    _safetensors(ruta, {"w": ("F32", [3, 4], 4)})
    datos = ruta.read_bytes()
    estado, fuente, error = cargar_modelo({}, {"archivo": ("m.safetensors", datos)})
    assert error is None
    assert estado["resumen"]["num_tensores"] == 1
    assert estado["resumen"]["total_params"] == 12


def test_cargar_modelo_ruta_local(tmp_path):
    ruta = tmp_path / "m.safetensors"
    _safetensors(ruta, {"w": ("F16", [2, 2], 2)})
    estado, fuente, error = cargar_modelo({"fuente": str(ruta)}, {})
    assert error is None
    assert estado["resumen"]["total_params"] == 4


def test_cargar_modelo_sin_entrada():
    estado, fuente, error = cargar_modelo({"fuente": ""}, {})
    assert estado is None
    assert error is not None


def test_inspeccionar_archivo_directo(tmp_path):
    ruta = tmp_path / "solo.safetensors"
    _safetensors(ruta, {"a": ("F32", [5], 4)})
    estado = inspeccionar(str(ruta))
    assert estado["resumen"]["num_tensores"] == 1
    assert estado["tensores"]["a"]["_archivo"] == "solo.safetensors"
