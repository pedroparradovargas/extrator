#!/usr/bin/env python3
"""
visor.py
Vista web del repositorio: muestra la estructura de TODO el código (archivos,
clases y funciones) y permite CARGAR UN MODELO de IA para inspeccionar su
estructura interna (arquitectura + tensores).

Solo usa la librería estándar de Python (no necesita Flask): funciona offline.

Uso:
    python visor.py                 # abre en http://localhost:8000
    python visor.py --port 9000
    python visor.py --raiz /ruta/al/repo

Luego abre el navegador en la dirección que se muestra. En el formulario
"Cargar modelo" puedes:
  - subir un archivo .safetensors,
  - escribir la ruta de una carpeta de modelo ya descargada, o
  - escribir un repo_id de HuggingFace (requiere acceso a internet).
"""

import argparse
import ast
import html
import os
import re
import tempfile

from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer

import inspector_modelos as im


RAIZ = os.path.dirname(os.path.abspath(__file__))

# Carpetas que no forman parte del código del proyecto.
IGNORAR = {".git", "__pycache__", ".pytest_cache", "venv", ".venv",
           "node_modules", "modelos"}


# ---------------------------------------------------------------------------
# Estructura del código del repositorio (vía AST)
# ---------------------------------------------------------------------------
def _simbolos(arbol):
    """Extrae funciones y clases (con sus métodos) de nivel superior."""
    salida = []
    for nodo in arbol.body:
        if isinstance(nodo, (ast.FunctionDef, ast.AsyncFunctionDef)):
            salida.append({"tipo": "def", "nombre": nodo.name,
                           "linea": nodo.lineno, "hijos": []})
        elif isinstance(nodo, ast.ClassDef):
            metodos = [
                {"tipo": "def", "nombre": m.name, "linea": m.lineno, "hijos": []}
                for m in nodo.body
                if isinstance(m, (ast.FunctionDef, ast.AsyncFunctionDef))
            ]
            salida.append({"tipo": "class", "nombre": nodo.name,
                           "linea": nodo.lineno, "hijos": metodos})
    return salida


def estructura_codigo(raiz):
    """Recorre el repo y devuelve la estructura de cada archivo .py.

    Devuelve una lista de dicts {ruta, lineas, simbolos}.
    """
    archivos = []
    for base, dirs, nombres in os.walk(raiz):
        dirs[:] = [d for d in dirs if d not in IGNORAR]
        for nombre in sorted(nombres):
            if not nombre.endswith(".py"):
                continue
            ruta = os.path.join(base, nombre)
            rel = os.path.relpath(ruta, raiz)
            try:
                with open(ruta, encoding="utf-8") as f:
                    fuente = f.read()
                arbol = ast.parse(fuente, filename=rel)
                simbolos = _simbolos(arbol)
                lineas = fuente.count("\n") + 1
            except (OSError, SyntaxError):
                simbolos, lineas = [], 0
            archivos.append({"ruta": rel, "lineas": lineas, "simbolos": simbolos})
    archivos.sort(key=lambda a: a["ruta"])
    return archivos


# ---------------------------------------------------------------------------
# Render HTML
# ---------------------------------------------------------------------------
ICONO = {"class": "🟦 class", "def": "🔧 def"}


def _render_simbolos(simbolos):
    if not simbolos:
        return ""
    filas = []
    for s in simbolos:
        etiqueta = ICONO.get(s["tipo"], s["tipo"])
        filas.append(
            f'<li><span class="sym {s["tipo"]}">{etiqueta} '
            f'{html.escape(s["nombre"])}</span> '
            f'<span class="ln">:{s["linea"]}</span>'
            f'{_render_simbolos(s["hijos"])}</li>'
        )
    return "<ul>" + "".join(filas) + "</ul>"


def render_estructura_codigo(raiz):
    archivos = estructura_codigo(raiz)
    total_lineas = sum(a["lineas"] for a in archivos)
    total_simbolos = sum(
        len(a["simbolos"]) + sum(len(s["hijos"]) for s in a["simbolos"])
        for a in archivos
    )
    bloques = [
        f'<p class="resumen">{len(archivos)} archivos · '
        f'{total_lineas} líneas · {total_simbolos} símbolos</p>'
    ]
    for a in archivos:
        bloques.append(
            f'<details open><summary>📄 {html.escape(a["ruta"])} '
            f'<span class="ln">({a["lineas"]} líneas)</span></summary>'
            f'{_render_simbolos(a["simbolos"]) or "<p class=vacio>(sin símbolos)</p>"}'
            f'</details>'
        )
    return "".join(bloques)


def render_modelo(estado, fuente, error=None):
    """Render del resultado de cargar un modelo (o un mensaje de error)."""
    if error:
        return f'<div class="error">⚠️ {html.escape(error)}</div>'
    if estado is None:
        return ('<p class="vacio">Aún no has cargado ningún modelo. '
                'Sube un .safetensors o indica una ruta / repo_id.</p>')

    res = estado["resumen"]
    partes = [f'<p class="resumen">Fuente: <code>{html.escape(str(fuente))}</code></p>']

    # Arquitectura
    config = estado["config"]
    if config:
        filas = "".join(
            f"<tr><td>{html.escape(etq)}</td><td>{html.escape(str(config[c]))}</td></tr>"
            for c, etq in im.CLAVES_ARQ if c in config
        )
        partes.append(f"<h3>Arquitectura</h3><table>{filas}</table>")

    # Resumen de tensores
    partes.append(
        '<h3>Tensores</h3>'
        f'<p class="resumen">{res["num_tensores"]} tensores · '
        f'{im._humano(res["total_params"])} parámetros · '
        f'{im._bytes_humano(res["total_bytes"])}</p>'
    )
    if estado["tensores"]:
        filas = []
        for i, (nombre, info) in enumerate(estado["tensores"].items()):
            if i >= 300:
                filas.append(f'<tr><td colspan=3>… '
                             f'({res["num_tensores"] - 300} más)</td></tr>')
                break
            shape = "×".join(str(d) for d in info.get("shape", [])) or "escalar"
            filas.append(
                f"<tr><td class=mono>{html.escape(nombre)}</td>"
                f"<td>{html.escape(info.get('dtype','?'))}</td>"
                f"<td>{shape}</td></tr>"
            )
        partes.append(
            "<table><tr><th>tensor</th><th>dtype</th><th>shape</th></tr>"
            + "".join(filas) + "</table>"
        )
    return "".join(partes)


PAGINA = """<!doctype html>
<html lang="es"><head><meta charset="utf-8">
<title>extrator · visor del repositorio</title>
<style>
 body {{ font-family: system-ui, sans-serif; margin: 0; background:#0d1117; color:#c9d1d9; }}
 header {{ background:#161b22; padding:16px 24px; border-bottom:1px solid #30363d; }}
 header h1 {{ margin:0; font-size:20px; }}
 header p {{ margin:4px 0 0; color:#8b949e; font-size:13px; }}
 main {{ display:flex; gap:0; align-items:flex-start; }}
 .col {{ padding:20px 24px; }}
 .izq {{ flex:1; border-right:1px solid #30363d; min-height:90vh; }}
 .der {{ flex:1; }}
 h2 {{ font-size:15px; text-transform:uppercase; letter-spacing:.05em; color:#8b949e; }}
 details {{ margin:4px 0; }}
 summary {{ cursor:pointer; padding:2px 0; }}
 ul {{ list-style:none; margin:2px 0 2px 18px; padding:0; border-left:1px solid #30363d; }}
 li {{ padding:1px 0 1px 10px; }}
 .sym.class {{ color:#79c0ff; }}
 .sym.def {{ color:#d2a8ff; }}
 .ln {{ color:#6e7681; font-size:12px; }}
 .resumen {{ color:#8b949e; font-size:13px; }}
 .vacio {{ color:#6e7681; font-style:italic; }}
 form {{ background:#161b22; border:1px solid #30363d; border-radius:8px; padding:16px; }}
 input[type=text], input[type=file] {{ width:100%; box-sizing:border-box; margin:6px 0;
   background:#0d1117; color:#c9d1d9; border:1px solid #30363d; border-radius:6px; padding:8px; }}
 button {{ background:#238636; color:#fff; border:0; border-radius:6px; padding:9px 16px;
   font-weight:600; cursor:pointer; }}
 table {{ border-collapse:collapse; width:100%; font-size:13px; margin:8px 0; }}
 td, th {{ border:1px solid #30363d; padding:5px 8px; text-align:left; }}
 th {{ background:#161b22; }}
 .mono {{ font-family:ui-monospace, monospace; }}
 .error {{ background:#3d1418; border:1px solid #f85149; color:#ff7b72;
   padding:12px; border-radius:6px; }}
 code {{ color:#79c0ff; }}
 h3 {{ margin:14px 0 4px; font-size:14px; }}
</style></head>
<body>
<header>
  <h1>🔍 extrator · visor del repositorio</h1>
  <p>Estructura de todo el código + cargador de modelos de IA</p>
</header>
<main>
  <section class="col izq">
    <h2>Estructura del código</h2>
    {codigo}
  </section>
  <section class="col der">
    <h2>Cargar modelo</h2>
    <form method="post" action="/cargar" enctype="multipart/form-data">
      <label>Subir archivo .safetensors / .gguf:</label>
      <input type="file" name="archivo" accept=".safetensors,.gguf">
      <label>…o ruta local (carpeta o archivo) / repo_id de HuggingFace:</label>
      <input type="text" name="fuente" placeholder="p.ej. ./modelos/gpt2  o  gpt2">
      <button type="submit">Cargar modelo</button>
    </form>
    <div class="resultado">{modelo}</div>
  </section>
</main>
</body></html>"""


# ---------------------------------------------------------------------------
# Parseo de multipart/form-data (subida de archivos, sin dependencias)
# ---------------------------------------------------------------------------
def parse_multipart(cuerpo, boundary):
    """Devuelve (campos, archivos). archivos[nombre] = (filename, bytes)."""
    campos, archivos = {}, {}
    delim = b"--" + boundary
    for parte in cuerpo.split(delim):
        if parte in (b"", b"--", b"--\r\n", b"\r\n"):
            continue
        if parte.startswith(b"\r\n"):
            parte = parte[2:]
        if parte.endswith(b"\r\n"):
            parte = parte[:-2]
        if b"\r\n\r\n" not in parte:
            continue
        cab, datos = parte.split(b"\r\n\r\n", 1)
        cab_txt = cab.decode("utf-8", "replace")
        m_nombre = re.search(r'name="([^"]*)"', cab_txt)
        if not m_nombre:
            continue
        nombre = m_nombre.group(1)
        m_archivo = re.search(r'filename="([^"]*)"', cab_txt)
        if m_archivo:
            if m_archivo.group(1):       # ignora el campo file vacío
                archivos[nombre] = (m_archivo.group(1), datos)
        else:
            campos[nombre] = datos.decode("utf-8", "replace").strip()
    return campos, archivos


# ---------------------------------------------------------------------------
# Carga del modelo a partir de la entrada del usuario
# ---------------------------------------------------------------------------
def cargar_modelo(campos, archivos):
    """Devuelve (estado, fuente, error)."""
    # 1) Archivo subido
    if "archivo" in archivos:
        filename, datos = archivos["archivo"]
        tmp = tempfile.mkdtemp(prefix="visor_modelo_")
        destino = os.path.join(tmp, os.path.basename(filename))
        with open(destino, "wb") as f:
            f.write(datos)
        try:
            return im.inspeccionar(destino), filename, None
        except Exception as e:                      # noqa: BLE001
            return None, filename, f"No se pudo leer '{filename}': {e}"

    fuente = (campos.get("fuente") or "").strip()
    if not fuente:
        return None, None, "Indica un archivo, una ruta o un repo_id."

    # 2) Ruta local existente
    if os.path.exists(fuente):
        try:
            return im.inspeccionar(fuente), fuente, None
        except Exception as e:                      # noqa: BLE001
            return None, fuente, str(e)

    # 3) repo_id de HuggingFace -> descargar
    try:
        ruta = im.descargar_modelo(fuente, solo_config=False)
        return im.inspeccionar(ruta), fuente, None
    except ValueError as e:
        return None, fuente, str(e)


# ---------------------------------------------------------------------------
# Servidor HTTP
# ---------------------------------------------------------------------------
class Handler(BaseHTTPRequestHandler):
    raiz = RAIZ

    def _html(self, modelo_html):
        return PAGINA.format(
            codigo=render_estructura_codigo(self.raiz),
            modelo=modelo_html,
        )

    def _responder(self, html_txt, codigo=200):
        cuerpo = html_txt.encode("utf-8")
        self.send_response(codigo)
        self.send_header("Content-Type", "text/html; charset=utf-8")
        self.send_header("Content-Length", str(len(cuerpo)))
        self.end_headers()
        self.wfile.write(cuerpo)

    def do_GET(self):
        if self.path.split("?")[0] not in ("/", "/index.html"):
            self._responder("<h1>404</h1>", 404)
            return
        self._responder(self._html(render_modelo(None, None)))

    def do_POST(self):
        if self.path != "/cargar":
            self._responder("<h1>404</h1>", 404)
            return
        longitud = int(self.headers.get("Content-Length", 0))
        cuerpo = self.rfile.read(longitud)
        tipo = self.headers.get("Content-Type", "")
        m = re.search(r"boundary=(.+)", tipo)
        if not m:
            self._responder(self._html(render_modelo(
                None, None, "Formato de formulario no válido.")))
            return
        boundary = m.group(1).strip().strip('"').encode("utf-8")
        campos, archivos = parse_multipart(cuerpo, boundary)
        estado, fuente, error = cargar_modelo(campos, archivos)
        self._responder(self._html(render_modelo(estado, fuente, error)))

    def log_message(self, *a):
        pass   # silencioso


def main(argv=None):
    p = argparse.ArgumentParser(description="Visor web del repositorio extrator.")
    p.add_argument("--port", type=int, default=8000)
    p.add_argument("--host", default="127.0.0.1")
    p.add_argument("--raiz", default=RAIZ, help="raíz del repo a inspeccionar")
    args = p.parse_args(argv)

    Handler.raiz = os.path.abspath(args.raiz)
    servidor = ThreadingHTTPServer((args.host, args.port), Handler)
    print(f"[*] Visor en marcha:  http://{args.host}:{args.port}")
    print("    Ctrl+C para detener.")
    try:
        servidor.serve_forever()
    except KeyboardInterrupt:
        print("\n[*] Detenido.")
        servidor.shutdown()


if __name__ == "__main__":
    main()
