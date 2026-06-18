"""
Fixtures de prueba.

Construye en disco un PE de 32 bits mínimo pero válido, sin necesitar un
compilador ni un .exe externo. Esto permite ejercitar las fases 1-4 de forma
determinista.
"""

import struct

import pytest


# Código x86 de la sección .text (entry point en VA 0x401000).
#   0x401000  55           push ebp
#   0x401001  89 e5        mov  ebp, esp
#   0x401003  31 c0        xor  eax, eax
#   0x401005  eb 02        jmp  0x401009      (salto incondicional hacia adelante)
#   0x401007  90           nop
#   0x401008  90           nop
#   0x401009  c3           ret
CODIGO_TEXT = bytes([
    0x55,
    0x89, 0xe5,
    0x31, 0xc0,
    0xeb, 0x02,
    0x90,
    0x90,
    0xc3,
])

IMAGE_BASE = 0x00400000
EP_RVA = 0x1000
EP_VA = IMAGE_BASE + EP_RVA
NOMBRE_SECCION = ".text"

FILE_ALIGN = 0x200
SECTION_ALIGN = 0x1000


def _construir_pe32():
    """Devuelve los bytes de un PE32 mínimo con una sección .text."""
    # --- DOS header (64 bytes) + stub hasta e_lfanew = 0x80 ---
    e_lfanew = 0x80
    dos = bytearray(b"\x00" * e_lfanew)
    dos[0:2] = b"MZ"
    struct.pack_into("<I", dos, 0x3C, e_lfanew)

    # --- Firma PE ---
    firma = b"PE\x00\x00"

    # --- IMAGE_FILE_HEADER (20 bytes) ---
    file_header = struct.pack(
        "<HHIIIHH",
        0x14c,      # Machine = x86
        1,          # NumberOfSections
        0,          # TimeDateStamp
        0,          # PointerToSymbolTable
        0,          # NumberOfSymbols
        0xE0,       # SizeOfOptionalHeader (224)
        0x0102,     # Characteristics (EXECUTABLE_IMAGE | 32BIT_MACHINE)
    )

    # --- IMAGE_OPTIONAL_HEADER32 (224 bytes) ---
    opt = b""
    opt += struct.pack("<H", 0x10b)          # Magic = PE32
    opt += struct.pack("<BB", 1, 0)          # Linker version
    opt += struct.pack("<I", FILE_ALIGN)     # SizeOfCode
    opt += struct.pack("<I", 0)              # SizeOfInitializedData
    opt += struct.pack("<I", 0)              # SizeOfUninitializedData
    opt += struct.pack("<I", EP_RVA)         # AddressOfEntryPoint
    opt += struct.pack("<I", EP_RVA)         # BaseOfCode
    opt += struct.pack("<I", 0x2000)         # BaseOfData
    opt += struct.pack("<I", IMAGE_BASE)     # ImageBase
    opt += struct.pack("<I", SECTION_ALIGN)  # SectionAlignment
    opt += struct.pack("<I", FILE_ALIGN)     # FileAlignment
    opt += struct.pack("<HH", 4, 0)          # OS version
    opt += struct.pack("<HH", 0, 0)          # Image version
    opt += struct.pack("<HH", 4, 0)          # Subsystem version
    opt += struct.pack("<I", 0)              # Win32VersionValue
    opt += struct.pack("<I", 0x2000)         # SizeOfImage
    opt += struct.pack("<I", FILE_ALIGN)     # SizeOfHeaders
    opt += struct.pack("<I", 0)              # CheckSum
    opt += struct.pack("<H", 3)              # Subsystem = CONSOLE
    opt += struct.pack("<H", 0)              # DllCharacteristics
    opt += struct.pack("<I", 0x100000)       # SizeOfStackReserve
    opt += struct.pack("<I", 0x1000)         # SizeOfStackCommit
    opt += struct.pack("<I", 0x100000)       # SizeOfHeapReserve
    opt += struct.pack("<I", 0x1000)         # SizeOfHeapCommit
    opt += struct.pack("<I", 0)              # LoaderFlags
    opt += struct.pack("<I", 16)             # NumberOfRvaAndSizes
    opt += b"\x00" * (16 * 8)                # 16 data directories vacíos
    assert len(opt) == 0xE0, len(opt)

    # --- IMAGE_SECTION_HEADER (40 bytes) ---
    nombre = NOMBRE_SECCION.encode().ljust(8, b"\x00")
    seccion = nombre
    seccion += struct.pack("<I", len(CODIGO_TEXT))  # VirtualSize
    seccion += struct.pack("<I", EP_RVA)            # VirtualAddress
    seccion += struct.pack("<I", FILE_ALIGN)        # SizeOfRawData
    seccion += struct.pack("<I", FILE_ALIGN)        # PointerToRawData
    seccion += struct.pack("<I", 0)                 # PointerToRelocations
    seccion += struct.pack("<I", 0)                 # PointerToLinenumbers
    seccion += struct.pack("<H", 0)                 # NumberOfRelocations
    seccion += struct.pack("<H", 0)                 # NumberOfLinenumbers
    seccion += struct.pack("<I", 0x60000020)        # Characteristics (code/exec/read)
    assert len(seccion) == 40, len(seccion)

    # --- Ensamblar cabeceras y rellenar hasta PointerToRawData ---
    cabeceras = bytes(dos) + firma + file_header + opt + seccion
    cabeceras = cabeceras.ljust(FILE_ALIGN, b"\x00")

    # --- Datos de la sección (rellenos a FILE_ALIGN) ---
    datos = CODIGO_TEXT.ljust(FILE_ALIGN, b"\x00")

    return cabeceras + datos


@pytest.fixture
def pe_minimo(tmp_path):
    """Escribe el PE mínimo en disco y devuelve sus metadatos esperados."""
    ruta = tmp_path / "muestra.exe"
    ruta.write_bytes(_construir_pe32())
    return {
        "ruta": str(ruta),
        "codigo": CODIGO_TEXT,
        "entry_point_va": EP_VA,
        "entry_point_rva": EP_RVA,
        "image_base": IMAGE_BASE,
        "nombre_seccion": NOMBRE_SECCION,
        "num_secciones": 1,
    }
