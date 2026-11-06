@echo off
cd /d "%~dp0"
powershell -NoProfile -ExecutionPolicy Bypass -File "%~dp0instalar.ps1" -SomenteApi
if errorlevel 1 (echo Falha na instalacao do modo API. & exit /b 1)
