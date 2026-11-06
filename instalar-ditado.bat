@echo off
cd /d "%~dp0"
".venv\Scripts\python.exe" -m pip install -r requirements-lock.txt
if errorlevel 1 goto failed
".venv\Scripts\python.exe" tools\prepare_dictation.py
if errorlevel 1 goto failed
echo Ditado instalado. Atualize a pagina do estudio.
pause
exit /b 0
:failed
echo Nao foi possivel preparar o ditado. Confira a conexao e tente novamente.
pause
exit /b 1
