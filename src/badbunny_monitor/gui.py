from __future__ import annotations

from html import escape
from wsgiref.simple_server import make_server
from urllib.parse import parse_qs

from .runtime_state import RuntimeState, RuntimeStateStore


HTML_TEMPLATE = """<!doctype html>
<html lang=\"es\"> 
<head>
  <meta charset=\"utf-8\" />
  <title>BadBunny Monitor - Configuración guiada</title>
  <style>
    body {{ font-family: Arial, sans-serif; margin: 24px; max-width: 950px; }}
    h1, h2 {{ color: #222; }}
    .card {{ border:1px solid #ddd; border-radius:8px; padding:16px; margin-bottom:16px; }}
    .ok {{ background:#e8f7e8; border-color:#6abf69; }}
    label {{ display:block; margin-top:8px; font-weight:600; }}
    input, select {{ width:100%; padding:8px; margin-top:4px; }}
    button {{ margin-top:12px; padding:10px 16px; font-weight:700; }}
    code {{ background:#f4f4f4; padding:2px 5px; border-radius:4px; }}
  </style>
</head>
<body>
  <h1>BadBunny Monitor · Asistente paso a paso</h1>
  <div class=\"card\">
    <h2>Paso 1 · Crear bot de Telegram</h2>
    <ol>
      <li>En Telegram abre <code>@BotFather</code>.</li>
      <li>Ejecuta <code>/newbot</code> y sigue instrucciones.</li>
      <li>Copia el <strong>token</strong> y pégalo en <code>.env</code> como <code>TELEGRAM_BOT_TOKEN</code>.</li>
      <li>Escribe a tu bot y obtén tu chat id (usuario/grupo), guárdalo como <code>TELEGRAM_CHAT_ID</code>.</li>
    </ol>
  </div>

  <div class=\"card\">
    <h2>Paso 2 · Definir precio máximo</h2>
    <p>Este valor se usa en <strong>modo REAL</strong> comparando contra precio unitario (total/entradas).</p>

    <form method=\"post\" action=\"/save\">
      <label>Precio máximo (€). Deja vacío para desactivar en modo real.</label>
      <input name=\"max_price_eur\" value=\"{max_price}\" placeholder=\"ej: 180\" />

      <label>Paso 3/4 · Modo de operación</label>
      <select name=\"operation_mode\">
        <option value=\"test\" {test_sel}>TEST: intenta carrito siempre</option>
        <option value=\"real\" {real_sel}>REAL: carrito solo si precio unitario <= máximo</option>
      </select>

      <button type=\"submit\">Guardar configuración de ejecución</button>
    </form>
  </div>

  <div class=\"card\">
    <h2>Paso 3 · Modo TEST</h2>
    <p>Intentará meter entrada en carrito aunque el precio supere el máximo y enviará mensaje de confirmación de intento de carrito para que entres a finalizar compra.</p>
  </div>

  <div class=\"card\">
    <h2>Paso 4 · Modo REAL</h2>
    <p>Hace el mismo proceso que test, pero solo cuando detecta entrada con <strong>precio unitario</strong> igual o inferior al máximo fijado.</p>
    <p>Si hay pack (ej. 3 entradas), calcula: <code>precio unitario = precio total / número de entradas</code>.</p>
  </div>

  {message_block}
</body>
</html>
"""


def build_page(state: RuntimeState, message: str = "") -> bytes:
    max_price = "" if state.max_price_eur is None else f"{state.max_price_eur:.2f}"
    message_block = ""
    if message:
        message_block = f"<div class='card ok'><strong>{escape(message)}</strong></div>"
    html = HTML_TEMPLATE.format(
        max_price=escape(max_price),
        test_sel="selected" if state.operation_mode == "test" else "",
        real_sel="selected" if state.operation_mode == "real" else "",
        message_block=message_block,
    )
    return html.encode("utf-8")


def create_app(state_path: str = "runtime_state.json"):
    store = RuntimeStateStore(state_path)

    def app(environ, start_response):
        method = environ.get("REQUEST_METHOD", "GET").upper()
        path = environ.get("PATH_INFO", "/")

        if method == "POST" and path == "/save":
            size = int(environ.get("CONTENT_LENGTH") or 0)
            body = environ["wsgi.input"].read(size).decode("utf-8")
            form = parse_qs(body)
            raw_price = (form.get("max_price_eur") or [""])[0].strip()
            raw_mode = (form.get("operation_mode") or ["real"])[0].strip().lower()
            max_price: float | None
            if raw_price:
                try:
                    max_price = float(raw_price.replace(",", "."))
                except ValueError:
                    max_price = None
            else:
                max_price = None
            if raw_mode not in {"real", "test"}:
                raw_mode = "real"
            store.save(RuntimeState(max_price_eur=max_price, operation_mode=raw_mode))
            page = build_page(store.load(), "Configuración guardada. El monitor la aplicará en el siguiente ciclo.")
            start_response("200 OK", [("Content-Type", "text/html; charset=utf-8")])
            return [page]

        state = store.load()
        page = build_page(state)
        start_response("200 OK", [("Content-Type", "text/html; charset=utf-8")])
        return [page]

    return app


def main() -> None:
    app = create_app()
    with make_server("0.0.0.0", 8080, app) as httpd:
        print("Interfaz disponible en http://localhost:8080")
        httpd.serve_forever()


if __name__ == "__main__":
    main()
