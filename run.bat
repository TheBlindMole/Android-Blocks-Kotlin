@echo off
REM Abre o DroidBlocks Studio sem instalar (modo portatil).
set "DIR=%~dp0"
where pyw >nul 2>nul && (start "" pyw -3 "%DIR%main.py" & exit /b)
where pythonw >nul 2>nul && (start "" pythonw "%DIR%main.py" & exit /b)
python "%DIR%main.py"
