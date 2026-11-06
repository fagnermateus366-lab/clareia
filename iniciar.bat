@echo off
chcp 65001 >nul
set PYTHONUTF8=1
cd /d "%~dp0"
if not exist ".venv\Scripts\python.exe" call instalar.bat
if errorlevel 1 exit /b 1
start "" "http://127.0.0.1:7860"
".venv\Scripts\python.exe" -c "import json,urllib.request; d=json.load(urllib.request.urlopen('http://127.0.0.1:7860/api/health',timeout=1)); assert d.get('ok') and d.get('local') and d.get('modelo')" >nul 2>&1
if not errorlevel 1 exit /b 0
".venv\Scripts\python.exe" -m overview serve --port 7860
