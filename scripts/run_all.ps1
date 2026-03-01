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
  Write-Error "No existe .env. Crea el archivo con tus credenciales reales antes de arrancar."
}

Write-Host "[INFO] Lanzando panel único en http://localhost:8080"
& $pythonExe -m badbunny_monitor.gui
