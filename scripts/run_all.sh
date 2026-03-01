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
  cat > .env <<'ENVEOF'
TELEGRAM_BOT_TOKEN=8777434243:AAFW5Il5ZP41V9z1MqVfqnQeNvukKCOUSWs
TELEGRAM_CHAT_ID=897260428
TICKETSWAP_QUERY=bad bunny madrid
TICKETSWAP_EVENT_URL=https://www.ticketswap.es/concert-tickets/bad-bunny-madrid-estadio-riyadh-air-metropolitano-2026-06-15-WEMPrvGmoQbQ9uQf93LDSU
POLL_INTERVAL_SECONDS=30
RUN_ONCE=false
REQUEST_TIMEOUT_SECONDS=12
MAX_PRICE_EUR=180
OPERATION_MODE=test
PROGRESS_TO_TELEGRAM=true
RUNTIME_STATE_PATH=runtime_state.json
TICKETSWAP_BUYER_COOKIE=session=replace_me
ENVEOF
  echo "[INFO] .env creado con valores iniciales (edítalo desde la UI)."
fi

echo "[INFO] Lanzando panel único en http://localhost:8080"
exec python -m badbunny_monitor.gui
