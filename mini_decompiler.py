#!/usr/bin/env python3
"""
mini_decompiler.py
Laboratorio de ingeniería inversa de ejecutables PE (.exe) — Fases 1 a 4.

  Fase 1: lectura y análisis de la estructura PE (cabeceras, secciones, imports)
  Fase 2: desensamblado (código máquina -> ensamblador) con Capstone
  Fase 3: detección de bloques básicos (inicio del grafo de flujo de control)
  Fase 4: construcción del grafo de flujo (CFG) y exportación a Graphviz DOT

IMPORTANTE: esto es un DESENSAMBLADOR/ANALIZADOR, no un decompilador que
reconstruya código C. Traduce el código máquina a ensamblador y dibuja el
flujo del programa, pero no genera pseudocódigo de alto nivel.

Instalación de dependencias:
    pip install -r requirements.txt        (pefile, capstone)

Uso:
    python mini_decompiler.py binario.exe
    python mini_decompiler.py binario.exe -o informe.txt --cfg flujo.dot -m 200

Nota didáctica: arranca con un .exe que tú mismo compiles (por ejemplo un
"hola mundo" en C con MinGW o MSVC) para poder verificar que la salida
coincide con lo que esperas. No analices binarios desconocidos fuera de
una máquina virtual aislada.
"""

import argparse
import sys

try:
    import pefile
    from capstone import (
        Cs, CS_ARCH_X86, CS_MODE_32, CS_MODE_64,
        CS_GRP_JUMP, CS_GRP_CALL, CS_GRP_RET,
    )
    from capstone.x86 import X86_OP_IMM
except ImportError:
    sys.exit("Faltan dependencias. Ejecuta: pip install -r requirements.txt")


# Mapa: tipo de máquina del PE -> (nombre legible, modo de Capstone)
MACHINE = {
    0x14c:  ("x86 (32-bit)", CS_MODE_32),
    0x8664: ("x64 (64-bit)", CS_MODE_64),
}

ANCHO = 64  # ancho de las líneas decorativas


def _titulo(texto):
    """Devuelve un encabezado decorado como lista de líneas."""
    return ["=" * ANCHO, f" {texto}", "=" * ANCHO]


# ---------------------------------------------------------------------------
# FASE 1: estructura del PE
# ---------------------------------------------------------------------------
def cargar_pe(ruta):
    """Carga el PE y devuelve (pe, nombre_arq, modo).

    Lanza ValueError con un mensaje claro en español si el archivo no existe,
    no es un PE válido o usa una arquitectura no soportada.
    """
    try:
        pe = pefile.PE(ruta)
    except FileNotFoundError:
        raise ValueError(f"No se encontró el archivo: {ruta}")
    except pefile.PEFormatError as e:
        raise ValueError(f"El archivo no es un PE válido ({ruta}): {e}")

    maquina = pe.FILE_HEADER.Machine
    if maquina not in MACHINE:
        raise ValueError(f"Arquitectura no soportada: {hex(maquina)}")
    nombre_arq, modo = MACHINE[maquina]
    return pe, nombre_arq, modo


def analizar_cabecera(pe, nombre_arq):
    """Extrae los datos clave de la cabecera PE como dict."""
    ep = pe.OPTIONAL_HEADER.AddressOfEntryPoint
    base = pe.OPTIONAL_HEADER.ImageBase
    return {
        "arquitectura": nombre_arq,
        "image_base": base,
        "entry_point_rva": ep,
        "entry_point_va": base + ep,
        "num_secciones": pe.FILE_HEADER.NumberOfSections,
    }


def analizar_secciones(pe):
    """Devuelve una lista de dicts, una por sección."""
    secciones = []
    for s in pe.sections:
        nombre = s.Name.rstrip(b"\x00").decode(errors="replace")
        secciones.append({
            "nombre": nombre,
            "rva": s.VirtualAddress,
            "tam_virtual": s.Misc_VirtualSize,
            "tam_crudo": s.SizeOfRawData,
        })
    return secciones


def analizar_imports(pe):
    """Devuelve una lista de (dll, [nombres de api]) o lista vacía."""
    importaciones = []
    try:
        pe.parse_data_directories()
        for entrada in pe.DIRECTORY_ENTRY_IMPORT:
            dll = entrada.dll.decode(errors="replace")
            apis = []
            for imp in entrada.imports[:8]:        # primeras 8 por DLL
                if imp.name:
                    apis.append(imp.name.decode(errors="replace"))
                else:
                    apis.append(f"ordinal {imp.ordinal}")
            importaciones.append((dll, apis))
    except AttributeError:
        pass
    return importaciones


def imprimir_cabecera(cab):
    lineas = _titulo("CABECERA PE")
    lineas.append(f"  Arquitectura      : {cab['arquitectura']}")
    lineas.append(f"  ImageBase         : {hex(cab['image_base'])}")
    lineas.append(f"  Entry Point (RVA) : {hex(cab['entry_point_rva'])}")
    lineas.append(f"  Entry Point (VA)  : {hex(cab['entry_point_va'])}")
    lineas.append(f"  N de secciones    : {cab['num_secciones']}")
    return lineas


def imprimir_secciones(secciones):
    lineas = [""] + _titulo("SECCIONES")
    lineas.append(f"  {'Nombre':<10}{'RVA':<12}{'Tam. virtual':<14}{'Tam. crudo':<12}")
    for s in secciones:
        lineas.append(
            f"  {s['nombre']:<10}{hex(s['rva']):<12}"
            f"{hex(s['tam_virtual']):<14}{hex(s['tam_crudo']):<12}"
        )
    return lineas


def imprimir_imports(importaciones):
    lineas = [""] + _titulo("IMPORTACIONES (APIs externas que usa el binario)")
    if not importaciones:
        lineas.append("  (sin tabla de importaciones)")
        return lineas
    for dll, apis in importaciones:
        lineas.append(f"  {dll}")
        for api in apis:
            lineas.append(f"      -> {api}")
    return lineas


# ---------------------------------------------------------------------------
# FASE 2: desensamblado
# ---------------------------------------------------------------------------
def seccion_de(pe, rva):
    """Devuelve la sección que contiene un RVA dado."""
    for s in pe.sections:
        ini = s.VirtualAddress
        fin = ini + max(s.Misc_VirtualSize, s.SizeOfRawData)
        if ini <= rva < fin:
            return s
    return None


def extraer_codigo_ep(pe):
    """Devuelve (bytes_de_codigo, direccion_virtual) desde el Entry Point.

    Devuelve (None, None) si no se encuentra la sección del entry point.
    """
    ep_rva = pe.OPTIONAL_HEADER.AddressOfEntryPoint
    base = pe.OPTIONAL_HEADER.ImageBase
    sec = seccion_de(pe, ep_rva)
    if sec is None:
        return None, None
    datos = sec.get_data()
    desplazamiento = ep_rva - sec.VirtualAddress
    return datos[desplazamiento:], base + ep_rva


def desensamblar_bytes(codigo, direccion, modo, max_inst=120):
    """Desensambla un bloque de bytes y recolecta los líderes de bloque.

    Devuelve (instrucciones, lideres). No imprime nada: es la lógica pura,
    fácil de probar de forma aislada.
    """
    md = Cs(CS_ARCH_X86, modo)
    md.detail = True                # necesario para leer grupos y operandos

    instrucciones = []
    lideres = {direccion}           # direcciones que inician un bloque básico

    for i, ins in enumerate(md.disasm(codigo, direccion)):
        instrucciones.append(ins)
        grupos = ins.groups
        # FASE 3 (recolección): marcar líderes de bloque
        if CS_GRP_JUMP in grupos or CS_GRP_CALL in grupos:
            # destino directo (operando inmediato) = inicio de bloque
            if len(ins.operands) == 1 and ins.operands[0].type == X86_OP_IMM:
                lideres.add(ins.operands[0].imm)
            # la instrucción siguiente también inicia bloque
            lideres.add(ins.address + ins.size)
        if CS_GRP_RET in grupos:
            lideres.add(ins.address + ins.size)

        if i + 1 >= max_inst:
            break

    return instrucciones, lideres


def desensamblar(pe, modo, max_inst=120):
    """Desensambla desde el Entry Point del PE."""
    codigo, direccion = extraer_codigo_ep(pe)
    if codigo is None:
        return [], {direccion}
    return desensamblar_bytes(codigo, direccion, modo, max_inst)


def imprimir_desensamblado(instrucciones, max_inst=120, recortado=False):
    lineas = [""] + _titulo("DESENSAMBLADO desde el Entry Point")
    if not instrucciones:
        lineas.append("  No se encontró la sección del entry point.")
        return lineas
    for ins in instrucciones:
        lineas.append(f"  0x{ins.address:08x}:  {ins.mnemonic:<8} {ins.op_str}")
    if recortado:
        lineas.append(f"  ... (cortado en {max_inst} instrucciones)")
    return lineas


# ---------------------------------------------------------------------------
# FASE 3 / 4: bloques básicos y grafo de flujo (CFG)
# ---------------------------------------------------------------------------
def construir_bloques(instrucciones, lideres):
    """Parte la lista de instrucciones en bloques básicos.

    Cada bloque es una lista de instrucciones contiguas; un bloque nuevo
    empieza en cada dirección que sea líder.
    """
    if not instrucciones:
        return []
    presentes = {ins.address for ins in instrucciones}
    # solo son líderes válidos los que apuntan a instrucciones realmente
    # desensambladas; el primer entry point siempre es líder.
    lideres_validos = (presentes & lideres) | {instrucciones[0].address}

    bloques = []
    actual = []
    for ins in instrucciones:
        if ins.address in lideres_validos and actual:
            bloques.append(actual)
            actual = []
        actual.append(ins)
    if actual:
        bloques.append(actual)
    return bloques


def calcular_aristas(bloques):
    """Calcula los sucesores de cada bloque.

    Devuelve un dict {direccion_inicio_bloque: [direcciones_sucesoras]}.
    Reglas:
      - ret                  -> sin sucesores
      - jmp incondicional    -> solo el destino del salto
      - salto condicional    -> destino + caída (fall-through)
      - call / instr. normal -> caída (fall-through)
    Solo se conservan destinos que sean inicio de algún bloque conocido.
    """
    inicios = {b[0].address for b in bloques}
    aristas = {}
    for b in bloques:
        inicio = b[0].address
        ultima = b[-1]
        grupos = ultima.groups
        siguiente = ultima.address + ultima.size

        destino_imm = None
        if (CS_GRP_JUMP in grupos or CS_GRP_CALL in grupos) and \
           len(ultima.operands) == 1 and ultima.operands[0].type == X86_OP_IMM:
            destino_imm = ultima.operands[0].imm

        suc = []
        if CS_GRP_RET in grupos:
            suc = []
        elif CS_GRP_JUMP in grupos:
            if destino_imm is not None:
                suc.append(destino_imm)
            if ultima.mnemonic != "jmp":          # condicional: también cae
                suc.append(siguiente)
        else:
            # call o instrucción normal: el flujo continúa en la siguiente
            suc.append(siguiente)

        aristas[inicio] = [d for d in suc if d in inicios]
    return aristas


def exportar_dot(bloques, aristas):
    """Genera el grafo de flujo en formato Graphviz DOT como string."""
    lineas = ["digraph cfg {", '  node [shape=box fontname="monospace"];']
    for b in bloques:
        inicio = b[0].address
        cuerpo = "\\l".join(
            f"0x{i.address:x}: {i.mnemonic} {i.op_str}".strip() for i in b
        )
        cuerpo = cuerpo.replace('"', r'\"')
        lineas.append(f'  "0x{inicio:x}" [label="{cuerpo}\\l"];')
    for origen, destinos in aristas.items():
        for d in destinos:
            lineas.append(f'  "0x{origen:x}" -> "0x{d:x}";')
    lineas.append("}")
    return "\n".join(lineas)


def imprimir_bloques(bloques):
    lineas = [""] + _titulo("BLOQUES BÁSICOS DETECTADOS (grafo de flujo)")
    for b in bloques:
        lineas.append(f"  Bloque en 0x{b[0].address:08x}  ({len(b)} instrucciones)")
    lineas.append(f"\n  Total: {len(bloques)} bloques (aprox.)")
    return lineas


# ---------------------------------------------------------------------------
# Orquestación
# ---------------------------------------------------------------------------
def generar_informe(pe, nombre_arq, modo, max_inst=120):
    """Construye el informe de texto completo y el CFG.

    Devuelve (texto_informe, bloques, aristas).
    """
    cab = analizar_cabecera(pe, nombre_arq)
    secciones = analizar_secciones(pe)
    importaciones = analizar_imports(pe)
    instrucciones, lideres = desensamblar(pe, modo, max_inst)
    recortado = len(instrucciones) >= max_inst
    bloques = construir_bloques(instrucciones, lideres)
    aristas = calcular_aristas(bloques)

    lineas = []
    lineas += imprimir_cabecera(cab)
    lineas += imprimir_secciones(secciones)
    lineas += imprimir_imports(importaciones)
    lineas += imprimir_desensamblado(instrucciones, max_inst, recortado)
    lineas += imprimir_bloques(bloques)
    return "\n".join(lineas), bloques, aristas


def parse_args(argv=None):
    p = argparse.ArgumentParser(
        description="Mini-analizador/desensamblador de ejecutables PE (.exe).",
    )
    p.add_argument("binario", help="ruta al ejecutable PE (.exe) a analizar")
    p.add_argument("-o", "--output", metavar="ARCHIVO",
                   help="guardar el informe de texto en un archivo")
    p.add_argument("-m", "--max-inst", type=int, default=120, metavar="N",
                   help="número máximo de instrucciones a desensamblar (def. 120)")
    p.add_argument("--cfg", metavar="ARCHIVO.dot",
                   help="exportar el grafo de flujo en formato Graphviz DOT")
    return p.parse_args(argv)


def main(argv=None):
    args = parse_args(argv)
    try:
        pe, nombre_arq, modo = cargar_pe(args.binario)
    except ValueError as e:
        print(f"Error: {e}", file=sys.stderr)
        return 1

    texto, bloques, aristas = generar_informe(pe, nombre_arq, modo, args.max_inst)
    print(texto)

    if args.output:
        try:
            with open(args.output, "w", encoding="utf-8") as f:
                f.write(texto + "\n")
            print(f"\n[+] Informe guardado en: {args.output}")
        except OSError as e:
            print(f"Error al escribir el informe: {e}", file=sys.stderr)
            return 1

    if args.cfg:
        try:
            with open(args.cfg, "w", encoding="utf-8") as f:
                f.write(exportar_dot(bloques, aristas) + "\n")
            print(f"[+] Grafo de flujo (DOT) guardado en: {args.cfg}")
            print("    Renderiza con:  dot -Tpng "
                  f"{args.cfg} -o flujo.png")
        except OSError as e:
            print(f"Error al escribir el CFG: {e}", file=sys.stderr)
            return 1

    return 0


if __name__ == "__main__":
    sys.exit(main())
