"""Pruebas de la Fase 0: identificación del tipo de binario."""

from mini_decompiler import detectar_por_firmas, detectar_tipo, cargar_pe


def test_firma_autoit():
    info = detectar_por_firmas(b"basura...AU3!EA06...mas basura")
    assert info is not None
    assert "AutoIt" in info["tipo"]
    assert info["fuente"] == "alto"


def test_firma_pyinstaller():
    info = detectar_por_firmas(b"....pyiboot01_bootstrap....")
    assert info is not None
    assert "PyInstaller" in info["tipo"]


def test_firma_go():
    info = detectar_por_firmas(b"\x00\x00Go build ID: abc\x00")
    assert info is not None
    assert "Go" in info["tipo"]


def test_sin_firma():
    assert detectar_por_firmas(b"texto cualquiera sin marcadores") is None


def test_pe_minimo_es_nativo(pe_minimo):
    pe, _, _ = cargar_pe(pe_minimo["ruta"])
    info = detectar_tipo(pe)
    # El PE mínimo no tiene runtime de ningún lenguaje gestionado.
    assert "nativo" in info["tipo"].lower()
    assert info["fuente"] == "no"
