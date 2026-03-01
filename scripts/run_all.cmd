@echo off
setlocal enabledelayedexpansion

set ROOT=%~dp0\..
cd /d %ROOT%

where python >nul 2>&1
if errorlevel 1 (
  echo [ERROR] Python no esta instalado o no esta en PATH.
  exit /b 1
)

if not exist .venv (
  echo [INFO] Creando entorno virtual...
  python -m venv .venv
)

set PYEXE=.venv\Scripts\python.exe

%PYEXE% -m pip install --upgrade pip >nul
%PYEXE% -m pip install -e .[dev]

if not exist .env (
  (
    echo TELEGRAM_BOT_TOKEN=8777434243:AAFW5Il5ZP41V9z1MqVfqnQeNvukKCOUSWs
    echo TELEGRAM_CHAT_ID=897260428
    echo TICKETSWAP_QUERY=bad bunny madrid
    echo TICKETSWAP_EVENT_URL=https://www.ticketswap.es/concert-tickets/bad-bunny-madrid-estadio-riyadh-air-metropolitano-2026-06-15-WEMPrvGmoQbQ9uQf93LDSU
    echo POLL_INTERVAL_SECONDS=30
    echo RUN_ONCE=false
    echo REQUEST_TIMEOUT_SECONDS=12
    echo MAX_PRICE_EUR=180
    echo OPERATION_MODE=test
    echo PROGRESS_TO_TELEGRAM=true
    echo RUNTIME_STATE_PATH=runtime_state.json
    echo TICKETSWAP_BUYER_COOKIE=session=replace_me
  ) > .env
  echo [INFO] .env creado con valores iniciales (editalo desde la UI).
)

echo [INFO] Lanzando panel unico en http://localhost:8080
%PYEXE% -m badbunny_monitor.gui
