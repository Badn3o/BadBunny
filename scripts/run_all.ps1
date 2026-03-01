$ErrorActionPreference = "Stop"

$Root = Split-Path -Parent $PSScriptRoot
Set-Location $Root

if (-not (Get-Command python -ErrorAction SilentlyContinue)) {
  Write-Error "Python no está instalado o no está en PATH."
}

if (-not (Test-Path ".venv")) {
  Write-Host "[INFO] Creando entorno virtual..."
  python -m venv .venv
}

$pythonExe = Join-Path $Root ".venv\Scripts\python.exe"

& $pythonExe -m pip install --upgrade pip | Out-Null
& $pythonExe -m pip install -e ".[dev]"

if (-not (Test-Path ".env")) {
@"
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
"@ | Set-Content -Encoding UTF8 .env
  Write-Host "[INFO] .env creado con valores iniciales (edítalo desde la UI)."
}

Write-Host "[INFO] Lanzando panel único en http://localhost:8080"
& $pythonExe -m badbunny_monitor.gui
