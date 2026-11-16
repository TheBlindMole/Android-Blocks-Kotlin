#!/bin/sh
# Instalador do DroidBlocks Studio para Linux e macOS.
# Uso: ./install.sh            (instalador grafico)
#      ./install.sh --silent   (instalacao sem interface)
set -e
DIR="$(cd "$(dirname "$0")" && pwd)"

# Procura um Python 3.9+ com Tkinter.
PY=""
for candidate in python3.13 python3.12 python3.11 python3.10 python3.9 python3 python; do
    if command -v "$candidate" >/dev/null 2>&1; then
        if "$candidate" -c "import sys, tkinter; sys.exit(0 if sys.version_info >= (3, 9) else 1)" >/dev/null 2>&1; then
            PY="$candidate"
            break
        fi
    fi
done

if [ -z "$PY" ]; then
    echo "Python 3.9+ com Tkinter nao encontrado."
    if [ "$(uname)" = "Darwin" ]; then
        echo "Instale o Python em https://www.python.org/downloads/ (ja inclui Tkinter)"
        echo "ou execute: brew install python-tk"
    else
        echo "Debian/Ubuntu: sudo apt install python3 python3-tk"
        echo "Fedora:        sudo dnf install python3 python3-tkinter"
        echo "Arch:          sudo pacman -S python tk"
    fi
    exit 1
fi

echo "Usando $($PY --version) em $(command -v $PY)"
if [ -z "$DISPLAY" ] && [ -z "$WAYLAND_DISPLAY" ] && [ "$(uname)" != "Darwin" ]; then
    echo "Sem interface grafica detectada: instalando em modo silencioso."
    exec "$PY" "$DIR/installer/installer.py" --silent "$@"
fi
exec "$PY" "$DIR/installer/installer.py" "$@"
