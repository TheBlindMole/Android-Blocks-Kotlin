#!/usr/bin/env python3
"""Ponto de entrada do DroidBlocks Studio.

Sem argumentos abre a interface grafica. Tambem funciona pela linha de comando:

    python main.py --list-templates
    python main.py --template "Loja online" --out ./saida [--views] [--package com.empresa.loja]
    python main.py --generate projeto.dbp --out ./saida [--zip]
"""

import argparse
import sys
from pathlib import Path

if sys.version_info < (3, 9):
    sys.exit("O DroidBlocks Studio requer Python 3.9 ou superior.")

sys.path.insert(0, str(Path(__file__).resolve().parent))


def cli(args):
    from droidblocks.catalog import templates
    from droidblocks.core.generator import generate, write_project, zip_project
    from droidblocks.core.storage import load_project

    if args.list_templates:
        for category in templates.categories():
            print(f"\n{category}")
            for tpl in templates.TEMPLATES:
                if tpl["category"] == category:
                    print(f"  - {tpl['name']}: {tpl['description']}")
        return 0
    if args.generate:
        project = load_project(args.generate)
    else:
        tpl = templates.find(args.template)
        if tpl is None:
            print(f"Modelo nao encontrado: {args.template}. Use --list-templates.")
            return 1
        project = templates.build_project(tpl, args.name or tpl["name"], args.package)
    if args.views:
        project.ui_mode = "views"
    result = generate(project)
    for level, message in result.resolved.diagnostics:
        print(f"[{level}] {message}")
    if result.resolved.errors:
        print("Geracao cancelada: corrija os erros acima.")
        return 1
    out = Path(args.out or ".").expanduser()
    root = write_project(result, out)
    print(f"Projeto gerado em {root} ({len(result.files)} arquivos).")
    if args.zip:
        print(f"Zip: {zip_project(result, out / (result.folder_name + '.zip'))}")
    return 0


def main():
    parser = argparse.ArgumentParser(description="DroidBlocks Studio - construtor no-code de apps Android")
    parser.add_argument("--list-templates", action="store_true", help="lista os modelos disponiveis")
    parser.add_argument("--template", help="gera um projeto a partir do modelo informado")
    parser.add_argument("--generate", help="gera o projeto a partir de um arquivo .dbp")
    parser.add_argument("--out", help="pasta de saida")
    parser.add_argument("--name", help="nome do app (com --template)")
    parser.add_argument("--package", help="pacote do app (com --template)")
    parser.add_argument("--views", action="store_true", help="usa XML Views em vez de Jetpack Compose")
    parser.add_argument("--zip", action="store_true", help="tambem cria um arquivo .zip")
    args = parser.parse_args()
    if args.list_templates or args.template or args.generate:
        sys.exit(cli(args))
    try:
        import tkinter  # noqa: F401
    except ImportError:
        sys.exit("Tkinter nao encontrado. No Linux instale o pacote python3-tk; "
                 "no macOS use o Python de python.org ou 'brew install python-tk'.")
    from droidblocks.ui.app import run
    run()


if __name__ == "__main__":
    main()
