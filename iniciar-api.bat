@echo off
cd /d "%~dp0"
if not exist ".venv\Scripts\python.exe" call instalar-api.bat
if errorlevel 1 exit /b 1
call iniciar.bat
