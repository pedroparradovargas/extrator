"""Pruebas de las Fases 3 y 4: bloques básicos y grafo de flujo."""

from capstone import CS_MODE_32

from mini_decompiler import (
    desensamblar_bytes, construir_bloques, calcular_aristas, exportar_dot,
)


CODIGO = bytes([
    0x55,             # 0x401000 push ebp
    0x89, 0xe5,       # 0x401001 mov ebp, esp
    0x31, 0xc0,       # 0x401003 xor eax, eax
    0xeb, 0x02,       # 0x401005 jmp 0x401009
    0x90,             # 0x401007 nop
    0x90,             # 0x401008 nop
    0xc3,             # 0x401009 ret
])
BASE = 0x401000


def _construir():
    instrucciones, lideres = desensamblar_bytes(CODIGO, BASE, CS_MODE_32, max_inst=7)
    bloques = construir_bloques(instrucciones, lideres)
    return bloques, calcular_aristas(bloques)


def test_tres_bloques():
    bloques, _ = _construir()
    inicios = [b[0].address for b in bloques]
    assert inicios == [0x401000, 0x401007, 0x401009]


def test_aristas():
    bloques, aristas = _construir()
    # el bloque 0x401000 termina en jmp incondicional -> solo 0x401009
    assert aristas[0x401000] == [0x401009]
    # el bloque 0x401007 (nops) cae al bloque 0x401009
    assert aristas[0x401007] == [0x401009]
    # el bloque 0x401009 termina en ret -> sin sucesores
    assert aristas[0x401009] == []


def test_construir_bloques_vacio():
    assert construir_bloques([], set()) == []


def test_exportar_dot():
    bloques, aristas = _construir()
    dot = exportar_dot(bloques, aristas)
    assert dot.startswith("digraph cfg {")
    assert dot.rstrip().endswith("}")
    assert '"0x401000"' in dot
    assert '"0x401000" -> "0x401009";' in dot
