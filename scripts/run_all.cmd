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
  echo [ERROR] No existe .env. Crea el archivo con tus credenciales reales antes de arrancar.
  exit /b 1
)

echo [INFO] Lanzando panel unico en http://localhost:8080
%PYEXE% -m badbunny_monitor.gui
