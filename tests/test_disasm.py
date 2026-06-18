"""Pruebas de la Fase 2: desensamblado y recolección de líderes."""

from capstone import CS_MODE_32

from mini_decompiler import desensamblar_bytes


# Mismo código que la fixture pe_minimo, con entry point en 0x401000.
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


def test_mnemonicos():
    instrucciones, _ = desensamblar_bytes(CODIGO, BASE, CS_MODE_32, max_inst=7)
    mnem = [i.mnemonic for i in instrucciones]
    assert mnem[:6] == ["push", "mov", "xor", "jmp", "nop", "nop"]


def test_direcciones():
    instrucciones, _ = desensamblar_bytes(CODIGO, BASE, CS_MODE_32, max_inst=7)
    direcciones = [i.address for i in instrucciones]
    assert 0x401000 in direcciones
    assert 0x401005 in direcciones   # jmp
    assert 0x401009 in direcciones   # ret


def test_lideres():
    _, lideres = desensamblar_bytes(CODIGO, BASE, CS_MODE_32, max_inst=7)
    # entry point, destino del jmp, caída tras el jmp y caída tras el ret
    assert 0x401000 in lideres       # entry point
    assert 0x401009 in lideres       # destino del jmp
    assert 0x401007 in lideres       # instrucción siguiente al jmp


def test_max_inst_limita():
    instrucciones, _ = desensamblar_bytes(CODIGO, BASE, CS_MODE_32, max_inst=3)
    assert len(instrucciones) == 3
