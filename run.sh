#!/bin/sh
# Abre o DroidBlocks Studio sem instalar (modo portatil).
DIR="$(cd "$(dirname "$0")" && pwd)"
for candidate in python3.13 python3.12 python3.11 python3.10 python3.9 python3 python; do
    if command -v "$candidate" >/dev/null 2>&1 && "$candidate" -c "import tkinter" >/dev/null 2>&1; then
        exec "$candidate" "$DIR/main.py" "$@"
    fi
done
echo "Python 3.9+ com Tkinter nao encontrado. Veja o README."
exit 1
