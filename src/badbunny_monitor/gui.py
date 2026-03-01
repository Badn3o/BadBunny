from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime, timezone
from html import escape
import os
from pathlib import Path
import subprocess
import threading
from wsgiref.simple_server import make_server
from urllib.parse import parse_qs

from .runtime_state import RuntimeState, RuntimeStateStore


@dataclass
class MonitorProcessState:
    process: subprocess.Popen[str] | None = None
    started_at_iso: str | None = None
    last_exit_code: int | None = None


class ProcessManager:
    def __init__(self, env_path: str = ".env", log_path: str = "monitor.log") -> None:
        self.env_path = Path(env_path)
        self.log_path = Path(log_path)
        self.state = MonitorProcessState()
        self._lock = threading.Lock()

    def read_env_text(self) -> str:
        if not self.env_path.exists():
            return ""
        return self.env_path.read_text(encoding="utf-8")

    def write_env_text(self, text: str) -> None:
        self.env_path.write_text(text.strip() + "\n", encoding="utf-8")

    def _load_env_dict(self) -> dict[str, str]:
        env = os.environ.copy()
        if not self.env_path.exists():
            return env
        for raw_line in self.env_path.read_text(encoding="utf-8").splitlines():
            line = raw_line.strip()
            if not line or line.startswith("#") or "=" not in line:
                continue
            key, value = line.split("=", 1)
            env[key.strip()] = value.strip().strip('"').strip("'")
        return env

    def start_monitor(self) -> str:
        with self._lock:
            if self.state.process and self.state.process.poll() is None:
                return "Monitor ya está en ejecución."
            env = self._load_env_dict()
            self.log_path.parent.mkdir(parents=True, exist_ok=True)
            log_file = self.log_path.open("a", encoding="utf-8")
            process = subprocess.Popen(
                ["python", "-m", "badbunny_monitor.main"],
                stdout=log_file,
                stderr=log_file,
                text=True,
                env=env,
            )
            self.state.process = process
            self.state.started_at_iso = datetime.now(timezone.utc).isoformat()
            self.state.last_exit_code = None
            return "Monitor iniciado."

    def stop_monitor(self) -> str:
        with self._lock:
            proc = self.state.process
            if not proc or proc.poll() is not None:
                return "Monitor no está en ejecución."
            proc.terminate()
            try:
                proc.wait(timeout=10)
            except subprocess.TimeoutExpired:
                proc.kill()
                proc.wait(timeout=5)
            self.state.last_exit_code = proc.returncode
            return f"Monitor detenido (exit={proc.returncode})."

    def restart_monitor(self) -> str:
        self.stop_monitor()
        return self.start_monitor()

    def health(self) -> str:
        proc = self.state.process
        if not proc:
            return "stopped"
        rc = proc.poll()
        if rc is None:
            return "running"
        self.state.last_exit_code = rc
        return f"exited({rc})"

    def tail_log(self, lines: int = 120) -> str:
        if not self.log_path.exists():
            return "(sin trazas todavía)"
        content = self.log_path.read_text(encoding="utf-8", errors="ignore").splitlines()
        return "\n".join(content[-lines:])


HTML_TEMPLATE = """<!doctype html>
<html lang=\"es\"> 
<head>
  <meta charset=\"utf-8\" />
  <title>BadBunny Monitor - Control UI</title>
  <style>
    body {{ font-family: Arial, sans-serif; margin: 24px; max-width: 1100px; }}
    h1, h2 {{ color: #222; }}
    .card {{ border:1px solid #ddd; border-radius:8px; padding:16px; margin-bottom:16px; }}
    .ok {{ background:#e8f7e8; border-color:#6abf69; }}
    .warn {{ background:#fff4e5; border-color:#e2a93b; }}
    label {{ display:block; margin-top:8px; font-weight:600; }}
    input, select, textarea {{ width:100%; padding:8px; margin-top:4px; }}
    textarea {{ min-height: 280px; font-family: monospace; }}
    .actions button {{ margin-right:8px; margin-top:12px; padding:10px 16px; font-weight:700; }}
    pre {{ background:#0f172a; color:#e2e8f0; padding:12px; border-radius:8px; overflow:auto; max-height: 420px; }}
  </style>
</head>
<body>
  <h1>BadBunny Monitor · Panel único</h1>
  <div class=\"card\">
    <h2>Estado proceso</h2>
    <p><strong>Estado:</strong> {status}</p>
    <p><strong>Arrancado en:</strong> {started_at}</p>
    <p><strong>Último exit code:</strong> {exit_code}</p>
    <form method=\"post\" action=\"/control\" class=\"actions\">
      <button name=\"action\" value=\"start\" type=\"submit\">Iniciar monitor</button>
      <button name=\"action\" value=\"restart\" type=\"submit\">Reiniciar monitor</button>
      <button name=\"action\" value=\"stop\" type=\"submit\">Detener monitor</button>
    </form>
  </div>

  <div class=\"card\">
    <h2>Editor .env</h2>
    <p>Edita configuración y reinicia desde aquí. Incluye token/chat, query, URL de evento, modo y cookies.</p>
    <form method=\"post\" action=\"/save-env\" class=\"actions\">
      <textarea name=\"env_text\">{env_text}</textarea>
      <button name=\"action\" value=\"save\" type=\"submit\">Guardar .env</button>
      <button name=\"action\" value=\"save_restart\" type=\"submit\">Guardar y relanzar todo</button>
    </form>
  </div>

  <div class=\"card\">
    <h2>Traza en vivo (monitor.log)</h2>
    <pre>{trace_text}</pre>
  </div>

  {message_block}
</body>
</html>
"""


def build_page(manager: ProcessManager, message: str = "") -> bytes:
    message_block = ""
    if message:
        message_block = f"<div class='card ok'><strong>{escape(message)}</strong></div>"
    health = manager.health()
    started = manager.state.started_at_iso or "N/A"
    exit_code = "N/A" if manager.state.last_exit_code is None else str(manager.state.last_exit_code)
    html = HTML_TEMPLATE.format(
        status=escape(health),
        started_at=escape(started),
        exit_code=escape(exit_code),
        env_text=escape(manager.read_env_text()),
        trace_text=escape(manager.tail_log()),
        message_block=message_block,
    )
    return html.encode("utf-8")


def create_app(state_path: str = "runtime_state.json", env_path: str = ".env"):
    _ = RuntimeStateStore(state_path)
    manager = ProcessManager(env_path=env_path, log_path="monitor.log")

    def app(environ, start_response):
        method = environ.get("REQUEST_METHOD", "GET").upper()
        path = environ.get("PATH_INFO", "/")

        if method == "POST" and path == "/save-env":
            size = int(environ.get("CONTENT_LENGTH") or 0)
            body = environ["wsgi.input"].read(size).decode("utf-8")
            form = parse_qs(body)
            env_text = (form.get("env_text") or [""])[0]
            action = (form.get("action") or ["save"])[0]
            manager.write_env_text(env_text)
            message = "Archivo .env guardado."
            if action == "save_restart":
                message = manager.restart_monitor()
                message = f".env guardado. {message}"
            page = build_page(manager, message)
            start_response("200 OK", [("Content-Type", "text/html; charset=utf-8")])
            return [page]

        if method == "POST" and path == "/control":
            size = int(environ.get("CONTENT_LENGTH") or 0)
            body = environ["wsgi.input"].read(size).decode("utf-8")
            form = parse_qs(body)
            action = (form.get("action") or [""])[0]
            if action == "start":
                message = manager.start_monitor()
            elif action == "restart":
                message = manager.restart_monitor()
            elif action == "stop":
                message = manager.stop_monitor()
            else:
                message = "Acción no válida"
            page = build_page(manager, message)
            start_response("200 OK", [("Content-Type", "text/html; charset=utf-8")])
            return [page]

        page = build_page(manager)
        start_response("200 OK", [("Content-Type", "text/html; charset=utf-8")])
        return [page]

    return app, manager


def main() -> None:
    app, manager = create_app()
    manager.start_monitor()
    with make_server("0.0.0.0", 8080, app) as httpd:
        print("Panel en http://localhost:8080")
        httpd.serve_forever()


if __name__ == "__main__":
    main()
