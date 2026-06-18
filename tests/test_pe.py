"""Pruebas de la Fase 1: análisis de la estructura PE."""

from mini_decompiler import (
    cargar_pe, analizar_cabecera, analizar_secciones, seccion_de,
)


def test_cargar_pe_arquitectura(pe_minimo):
    pe, nombre_arq, modo = cargar_pe(pe_minimo["ruta"])
    assert nombre_arq == "x86 (32-bit)"


def test_cabecera(pe_minimo):
    pe, nombre_arq, _ = cargar_pe(pe_minimo["ruta"])
    cab = analizar_cabecera(pe, nombre_arq)
    assert cab["image_base"] == pe_minimo["image_base"]
    assert cab["entry_point_rva"] == pe_minimo["entry_point_rva"]
    assert cab["entry_point_va"] == pe_minimo["entry_point_va"]
    assert cab["num_secciones"] == pe_minimo["num_secciones"]


def test_secciones(pe_minimo):
    pe, _, _ = cargar_pe(pe_minimo["ruta"])
    secciones = analizar_secciones(pe)
    assert len(secciones) == 1
    assert secciones[0]["nombre"] == pe_minimo["nombre_seccion"]
    assert secciones[0]["rva"] == pe_minimo["entry_point_rva"]


def test_seccion_de_contiene_entry_point(pe_minimo):
    pe, _, _ = cargar_pe(pe_minimo["ruta"])
    sec = seccion_de(pe, pe_minimo["entry_point_rva"])
    assert sec is not None
    assert sec.Name.rstrip(b"\x00").decode() == pe_minimo["nombre_seccion"]


def test_archivo_inexistente():
    import pytest
    with pytest.raises(ValueError, match="No se encontró"):
        cargar_pe("/no/existe/este/archivo.exe")


def test_archivo_no_pe(tmp_path):
    import pytest
    basura = tmp_path / "basura.exe"
    basura.write_bytes(b"esto no es un PE en absoluto")
    with pytest.raises(ValueError, match="no es un PE"):
        cargar_pe(str(basura))
