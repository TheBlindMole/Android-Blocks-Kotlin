#!/usr/bin/env python3
"""Gera um executavel independente (sem precisar de Python instalado) e o pacote de instalacao.

Requer apenas o PyInstaller na maquina de build:  pip install pyinstaller
Execute no sistema de destino (o PyInstaller nao faz compilacao cruzada):

    Windows:  python installer/build_executable.py    -> dist/DroidBlocksStudio.exe e, com Inno Setup,
                                                         dist/DroidBlocksStudio-Setup.exe
    macOS:    python3 installer/build_executable.py   -> dist/DroidBlocks Studio.app e .dmg
    Linux:    python3 installer/build_executable.py   -> dist/droidblocks-studio, .tar.gz e .deb (se dpkg-deb)
"""

import platform
import shutil
import subprocess
import sys
import tarfile
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT))

from droidblocks import __version__ as VERSION  # noqa: E402
from droidblocks.core.png import render_icon, build_ico, build_icns  # noqa: E402

DIST = ROOT / "dist"
BUILD = ROOT / "build"
SYSTEM = platform.system()


def icons():
    folder = BUILD / "icons"
    folder.mkdir(parents=True, exist_ok=True)
    pngs = {s: render_icon(s, "#2F81F7") for s in (16, 32, 48, 64, 128, 256, 512)}
    (folder / "droidblocks.png").write_bytes(pngs[256])
    (folder / "droidblocks.ico").write_bytes(build_ico({s: pngs[s] for s in (16, 32, 48, 64, 128, 256)}))
    (folder / "droidblocks.icns").write_bytes(build_icns(pngs))
    return folder


def pyinstaller(icon_folder):
    try:
        import PyInstaller.__main__ as pyi
    except ImportError:
        sys.exit("PyInstaller nao encontrado. Instale com: pip install pyinstaller")
    sep = ";" if SYSTEM == "Windows" else ":"
    icon = {"Windows": "droidblocks.ico", "Darwin": "droidblocks.icns"}.get(SYSTEM, "droidblocks.png")
    name = "DroidBlocks Studio" if SYSTEM == "Darwin" else ("DroidBlocksStudio" if SYSTEM == "Windows" else "droidblocks-studio")
    args = [
        str(ROOT / "main.py"), "--name", name, "--windowed", "--noconfirm", "--clean",
        "--distpath", str(DIST), "--workpath", str(BUILD / "pyinstaller"), "--specpath", str(BUILD),
        "--icon", str(icon_folder / icon),
        "--add-data", f"{ROOT / 'droidblocks' / 'assets'}{sep}droidblocks/assets",
        "--collect-submodules", "droidblocks",
    ]
    if SYSTEM != "Darwin":
        args.append("--onefile")
    else:
        args += ["--osx-bundle-identifier", "com.droidblocks.studio"]
    pyi.run(args)
    return name


def package_windows(name):
    iss = ROOT / "installer" / "windows" / "setup.iss"
    compiler = shutil.which("iscc") or shutil.which("ISCC")
    default = Path(r"C:\Program Files (x86)\Inno Setup 6\ISCC.exe")
    if not compiler and default.exists():
        compiler = str(default)
    if compiler:
        subprocess.run([compiler, f"/DAppVersion={VERSION}", f"/DSourceExe={DIST / (name + '.exe')}",
                        f"/DIconFile={BUILD / 'icons' / 'droidblocks.ico'}", f"/DOutputDir={DIST}", str(iss)], check=True)
        print("Instalador criado em dist/DroidBlocksStudio-Setup.exe")
    else:
        print("Inno Setup nao encontrado: o executavel portatil esta em dist/. "
              "Para gerar o Setup.exe instale o Inno Setup 6 (gratuito) e rode novamente.")


def package_mac(name):
    app = DIST / f"{name}.app"
    dmg = DIST / f"DroidBlocksStudio-{VERSION}.dmg"
    if shutil.which("hdiutil") and app.exists():
        staging = BUILD / "dmg"
        if staging.exists():
            shutil.rmtree(staging)
        staging.mkdir(parents=True)
        shutil.copytree(app, staging / app.name, symlinks=True)
        (staging / "Applications").symlink_to("/Applications")
        subprocess.run(["hdiutil", "create", "-volname", "DroidBlocks Studio", "-srcfolder", str(staging),
                        "-ov", "-format", "UDZO", str(dmg)], check=True)
        print(f"Imagem de disco criada: {dmg}")


def package_linux(name):
    binary = DIST / name
    if not binary.exists():
        return
    icon = BUILD / "icons" / "droidblocks.png"
    tar_path = DIST / f"droidblocks-studio-{VERSION}-linux-{platform.machine()}.tar.gz"
    with tarfile.open(tar_path, "w:gz") as tar:
        tar.add(binary, arcname=f"droidblocks-studio/{name}")
        tar.add(icon, arcname="droidblocks-studio/droidblocks.png")
    print(f"Pacote criado: {tar_path}")
    if shutil.which("dpkg-deb"):
        root = BUILD / "deb"
        if root.exists():
            shutil.rmtree(root)
        (root / "DEBIAN").mkdir(parents=True)
        (root / "usr" / "bin").mkdir(parents=True)
        (root / "usr" / "share" / "applications").mkdir(parents=True)
        (root / "usr" / "share" / "icons" / "hicolor" / "256x256" / "apps").mkdir(parents=True)
        shutil.copy2(binary, root / "usr" / "bin" / "droidblocks-studio")
        shutil.copy2(icon, root / "usr" / "share" / "icons" / "hicolor" / "256x256" / "apps" / "droidblocks-studio.png")
        arch = {"x86_64": "amd64", "aarch64": "arm64"}.get(platform.machine(), platform.machine())
        (root / "DEBIAN" / "control").write_text(
            f"Package: droidblocks-studio\nVersion: {VERSION}\nSection: devel\nPriority: optional\n"
            f"Architecture: {arch}\nMaintainer: DroidBlocks <contato@droidblocks.local>\n"
            "Description: Construtor no-code de aplicativos Android em Kotlin\n"
            " Monte aplicativos Android por blocos e gere projetos completos para o Android Studio.\n",
            encoding="utf-8")
        (root / "usr" / "share" / "applications" / "droidblocks-studio.desktop").write_text(
            "[Desktop Entry]\nType=Application\nName=DroidBlocks Studio\n"
            "Comment=Crie aplicativos Android em Kotlin montando blocos\nExec=droidblocks-studio\n"
            "Icon=droidblocks-studio\nTerminal=false\nCategories=Development;IDE;\n", encoding="utf-8")
        deb = DIST / f"droidblocks-studio_{VERSION}_{arch}.deb"
        subprocess.run(["dpkg-deb", "--build", "--root-owner-group", str(root), str(deb)], check=True)
        print(f"Pacote Debian criado: {deb}")


def main():
    DIST.mkdir(exist_ok=True)
    folder = icons()
    name = pyinstaller(folder)
    if SYSTEM == "Windows":
        package_windows(name)
    elif SYSTEM == "Darwin":
        package_mac(name)
    else:
        package_linux(name)
    print("Concluido. Arquivos em", DIST)


if __name__ == "__main__":
    main()
