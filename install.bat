@echo off
REM Instalador do DroidBlocks Studio para Windows.
REM Uso: install.bat            (instalador grafico)
REM      install.bat --silent   (instalacao sem interface)
setlocal
set "DIR=%~dp0"

where py >nul 2>nul
if %errorlevel%==0 (
    py -3 -c "import sys, tkinter; sys.exit(0 if sys.version_info >= (3, 9) else 1)" >nul 2>nul
    if not errorlevel 1 (
        py -3 "%DIR%installer\installer.py" %*
        goto :fim
    )
)

where python >nul 2>nul
if %errorlevel%==0 (
    python -c "import sys, tkinter; sys.exit(0 if sys.version_info >= (3, 9) else 1)" >nul 2>nul
    if not errorlevel 1 (
        python "%DIR%installer\installer.py" %*
        goto :fim
    )
)

echo Python 3.9 ou superior nao foi encontrado.
echo Baixe em https://www.python.org/downloads/ e marque "Add python.exe to PATH" e "tcl/tk".
pause
exit /b 1

:fim
endlocal
