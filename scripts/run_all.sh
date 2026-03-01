#!/usr/bin/env bash
set -euo pipefail

ROOT_DIR="$(cd "$(dirname "$0")/.." && pwd)"
cd "$ROOT_DIR"

if ! command -v python3 >/dev/null 2>&1; then
  echo "[ERROR] python3 no está instalado"
  exit 1
fi

if [ ! -d ".venv" ]; then
  echo "[INFO] Creando entorno virtual..."
  python3 -m venv .venv
fi

# shellcheck disable=SC1091
source .venv/bin/activate

python -m pip install --upgrade pip >/dev/null
python -m pip install -e .[dev]

if [ ! -f .env ]; then
  echo "[ERROR] No existe .env. Crea el archivo con tus credenciales reales antes de arrancar."
  echo "[TIP] Puedes copiar .env.example y rellenarlo con tus valores."
  exit 1
fi

echo "[INFO] Lanzando panel único en http://localhost:8080"
exec python -m badbunny_monitor.gui
