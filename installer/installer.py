#!/usr/bin/env python3
"""Instalador do DroidBlocks Studio para Windows, macOS e Linux.

Interface grafica (Tkinter) ou modo silencioso:
    python installer.py                 abre o instalador grafico
    python installer.py --silent        instala com as opcoes padrao
    python installer.py --silent --dir /opt/droidblocks --no-desktop
    python installer.py --uninstall     remove a instalacao registrada

O instalador copia o aplicativo, gera os icones, cria atalhos no menu do sistema,
na area de trabalho e um comando 'droidblocks' no terminal. Nada e baixado da internet.
"""

import argparse
import json
import os
import platform
import shutil
import subprocess
import sys
import threading
from pathlib import Path

SOURCE = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(SOURCE))

APP_NAME = "DroidBlocks Studio"
APP_ID = "droidblocks-studio"
SYSTEM = platform.system()
MANIFEST_NAME = "install-manifest.json"
COPY_ITEMS = ["main.py", "droidblocks", "README.md", "LICENSE", "requirements.txt", "installer"]

try:
    from droidblocks import __version__ as VERSION
except Exception:
    VERSION = "1.1.0"


# ----------------------------------------------------------------- caminhos padrao

def default_install_dir():
    home = Path.home()
    if SYSTEM == "Windows":
        base = Path(os.environ.get("LOCALAPPDATA", home / "AppData" / "Local"))
        return base / "Programs" / APP_NAME
    if SYSTEM == "Darwin":
        return home / "Library" / "Application Support" / "DroidBlocks" / "app"
    return Path(os.environ.get("XDG_DATA_HOME") or home / ".local" / "share") / APP_ID


def desktop_dir():
    home = Path.home()
    if SYSTEM == "Windows":
        try:
            out = subprocess.run(["powershell", "-NoProfile", "-Command",
                                  "[Environment]::GetFolderPath('Desktop')"],
                                 capture_output=True, text=True, timeout=20)
            if out.stdout.strip():
                return Path(out.stdout.strip())
        except Exception:
            pass
        return home / "Desktop"
    if SYSTEM == "Linux":
        try:
            out = subprocess.run(["xdg-user-dir", "DESKTOP"], capture_output=True, text=True, timeout=5)
            if out.stdout.strip():
                return Path(out.stdout.strip())
        except Exception:
            pass
    return home / "Desktop"


def try_run(command):
    """Executa um comando opcional do sistema, ignorando se nao existir."""
    try:
        subprocess.run(command, capture_output=True, timeout=30)
    except (OSError, subprocess.SubprocessError):
        pass


def python_gui_executable():
    """Interpretador usado pelos atalhos (pythonw no Windows evita a janela do console)."""
    exe = Path(sys.executable)
    if SYSTEM == "Windows":
        candidate = exe.with_name("pythonw.exe")
        if candidate.exists():
            return candidate
    return exe


# ----------------------------------------------------------------- etapas

class Installer:
    """Executa a instalacao e registra tudo o que foi criado para a desinstalacao."""

    def __init__(self, target, desktop=True, menu=True, command=True, log=print):
        self.target = Path(target).expanduser()
        self.desktop = desktop
        self.menu = menu
        self.command = command
        self.log = log
        self.created = []

    def run(self):
        self.check_requirements()
        self.copy_files()
        icons = self.make_icons()
        python = python_gui_executable()
        main = self.target / "main.py"
        if SYSTEM == "Windows":
            self.windows_shortcuts(python, main, icons)
        elif SYSTEM == "Darwin":
            self.mac_app(python, main, icons)
        else:
            self.linux_entries(python, main, icons)
        self.write_uninstaller(python)
        self.save_manifest()
        self.log("Instalacao concluida.")
        return self.target

    def check_requirements(self):
        if sys.version_info < (3, 9):
            raise RuntimeError("E necessario Python 3.9 ou superior.")
        try:
            import tkinter  # noqa: F401
        except ImportError:
            hint = {"Linux": "Instale com: sudo apt install python3-tk (ou dnf install python3-tkinter).",
                    "Darwin": "Use o Python de python.org ou: brew install python-tk."}.get(SYSTEM, "")
            raise RuntimeError("Tkinter nao encontrado. " + hint)
        self.log(f"Python {platform.python_version()} com Tkinter: ok")

    def copy_files(self):
        self.log(f"Copiando arquivos para {self.target}")
        self.target.mkdir(parents=True, exist_ok=True)
        ignore = shutil.ignore_patterns("__pycache__", "*.pyc", ".git", "dist", "build", "*.spec")
        for item in COPY_ITEMS:
            source = SOURCE / item
            dest = self.target / item
            if not source.exists():
                continue
            if source.is_dir():
                if dest.exists():
                    shutil.rmtree(dest)
                shutil.copytree(source, dest, ignore=ignore)
            else:
                shutil.copy2(source, dest)
        self.created.append(str(self.target))

    def make_icons(self):
        from droidblocks.core.png import render_icon, build_ico, build_icns
        folder = self.target / "icons"
        folder.mkdir(exist_ok=True)
        pngs = {size: render_icon(size, "#2F81F7") for size in (16, 32, 48, 64, 128, 256, 512)}
        (folder / "droidblocks.png").write_bytes(pngs[256])
        (folder / "droidblocks.ico").write_bytes(build_ico({s: pngs[s] for s in (16, 32, 48, 64, 128, 256)}))
        (folder / "droidblocks.icns").write_bytes(build_icns(pngs))
        self.log("Icones gerados")
        return folder

    # ----- Windows
    def _powershell_shortcut(self, link, python, main, icon):
        script = (
            "$s = (New-Object -ComObject WScript.Shell).CreateShortcut($env:DB_LINK);"
            "$s.TargetPath = $env:DB_TARGET; $s.Arguments = $env:DB_ARGS;"
            "$s.WorkingDirectory = $env:DB_WORKDIR; $s.IconLocation = $env:DB_ICON;"
            "$s.Description = 'DroidBlocks Studio'; $s.Save()")
        env = dict(os.environ, DB_LINK=str(link), DB_TARGET=str(python), DB_ARGS=f'"{main}"',
                   DB_WORKDIR=str(self.target), DB_ICON=str(icon))
        subprocess.run(["powershell", "-NoProfile", "-ExecutionPolicy", "Bypass", "-Command", script],
                       check=True, env=env, capture_output=True, timeout=60)
        self.created.append(str(link))

    def windows_shortcuts(self, python, main, icons):
        icon = icons / "droidblocks.ico"
        if self.menu:
            programs = Path(os.environ["APPDATA"]) / "Microsoft" / "Windows" / "Start Menu" / "Programs"
            programs.mkdir(parents=True, exist_ok=True)
            self._powershell_shortcut(programs / f"{APP_NAME}.lnk", python, main, icon)
            self.log("Atalho criado no Menu Iniciar")
        if self.desktop:
            self._powershell_shortcut(desktop_dir() / f"{APP_NAME}.lnk", python, main, icon)
            self.log("Atalho criado na Area de Trabalho")
        if self.command:
            bat = self.target / "droidblocks.bat"
            bat.write_text(f'@echo off\r\n"{sys.executable}" "{main}" %*\r\n', encoding="utf-8")
            self.log(f"Comando de terminal: {bat}")
        try:
            import winreg
            key_path = rf"Software\Microsoft\Windows\CurrentVersion\Uninstall\{APP_ID}"
            with winreg.CreateKey(winreg.HKEY_CURRENT_USER, key_path) as key:
                winreg.SetValueEx(key, "DisplayName", 0, winreg.REG_SZ, APP_NAME)
                winreg.SetValueEx(key, "DisplayVersion", 0, winreg.REG_SZ, VERSION)
                winreg.SetValueEx(key, "Publisher", 0, winreg.REG_SZ, "DroidBlocks")
                winreg.SetValueEx(key, "InstallLocation", 0, winreg.REG_SZ, str(self.target))
                winreg.SetValueEx(key, "DisplayIcon", 0, winreg.REG_SZ, str(icon))
                winreg.SetValueEx(key, "UninstallString", 0, winreg.REG_SZ,
                                  f'"{python}" "{self.target / "uninstall.py"}"')
                winreg.SetValueEx(key, "NoModify", 0, winreg.REG_DWORD, 1)
                winreg.SetValueEx(key, "NoRepair", 0, winreg.REG_DWORD, 1)
            self.created.append("registry:" + key_path)
            self.log("Registrado em Aplicativos instalados do Windows")
        except Exception as exc:
            self.log(f"Aviso: nao foi possivel registrar no Windows ({exc})")

    # ----- macOS
    def mac_app(self, python, main, icons):
        apps = Path.home() / "Applications"
        bundle = apps / f"{APP_NAME}.app"
        if bundle.exists():
            shutil.rmtree(bundle)
        (bundle / "Contents" / "MacOS").mkdir(parents=True)
        (bundle / "Contents" / "Resources").mkdir(parents=True)
        shutil.copy2(icons / "droidblocks.icns", bundle / "Contents" / "Resources" / "AppIcon.icns")
        launcher = bundle / "Contents" / "MacOS" / "DroidBlocks"
        launcher.write_text(f'#!/bin/bash\ncd "{self.target}"\nexec "{python}" "{main}" "$@"\n', encoding="utf-8")
        launcher.chmod(0o755)
        (bundle / "Contents" / "Info.plist").write_text(f'''<?xml version="1.0" encoding="UTF-8"?>
<!DOCTYPE plist PUBLIC "-//Apple//DTD PLIST 1.0//EN" "http://www.apple.com/DTDs/PropertyList-1.0.dtd">
<plist version="1.0">
<dict>
    <key>CFBundleName</key><string>{APP_NAME}</string>
    <key>CFBundleDisplayName</key><string>{APP_NAME}</string>
    <key>CFBundleIdentifier</key><string>com.droidblocks.studio</string>
    <key>CFBundleVersion</key><string>{VERSION}</string>
    <key>CFBundleShortVersionString</key><string>{VERSION}</string>
    <key>CFBundleExecutable</key><string>DroidBlocks</string>
    <key>CFBundleIconFile</key><string>AppIcon</string>
    <key>CFBundlePackageType</key><string>APPL</string>
    <key>NSHighResolutionCapable</key><true/>
    <key>LSMinimumSystemVersion</key><string>10.13</string>
</dict>
</plist>
''', encoding="utf-8")
        self.created.append(str(bundle))
        self.log(f"Aplicativo criado em {bundle}")
        if self.desktop:
            alias = desktop_dir() / f"{APP_NAME}.app"
            if alias.is_symlink() or alias.exists():
                alias.unlink()
            alias.symlink_to(bundle)
            self.created.append(str(alias))
            self.log("Atalho criado na Mesa")
        if self.command:
            self._unix_command(python, main)

    # ----- Linux
    def linux_entries(self, python, main, icons):
        data = Path(os.environ.get("XDG_DATA_HOME") or Path.home() / ".local" / "share")
        icon_dir = data / "icons" / "hicolor" / "256x256" / "apps"
        icon_dir.mkdir(parents=True, exist_ok=True)
        icon = icon_dir / f"{APP_ID}.png"
        shutil.copy2(icons / "droidblocks.png", icon)
        self.created.append(str(icon))
        entry = f"""[Desktop Entry]
Type=Application
Version=1.0
Name={APP_NAME}
GenericName=Construtor de apps Android
Comment=Crie aplicativos Android em Kotlin montando blocos
Exec="{python}" "{main}"
Path={self.target}
Icon={icon}
Terminal=false
Categories=Development;IDE;
Keywords=android;kotlin;nocode;app;
StartupWMClass=Tk
"""
        if self.menu:
            apps = data / "applications"
            apps.mkdir(parents=True, exist_ok=True)
            desktop_file = apps / f"{APP_ID}.desktop"
            desktop_file.write_text(entry, encoding="utf-8")
            desktop_file.chmod(0o755)
            self.created.append(str(desktop_file))
            try_run(["update-desktop-database", str(apps)])
            self.log("Atalho criado no menu de aplicativos")
        if self.desktop:
            desk = desktop_dir()
            if desk.exists():
                shortcut = desk / f"{APP_ID}.desktop"
                shortcut.write_text(entry, encoding="utf-8")
                shortcut.chmod(0o755)
                try_run(["gio", "set", str(shortcut), "metadata::trusted", "true"])
                self.created.append(str(shortcut))
                self.log("Atalho criado na area de trabalho")
        if self.command:
            self._unix_command(python, main)

    def _unix_command(self, python, main):
        bin_dir = Path.home() / ".local" / "bin"
        bin_dir.mkdir(parents=True, exist_ok=True)
        script = bin_dir / "droidblocks"
        script.write_text(f'#!/bin/sh\nexec "{python}" "{main}" "$@"\n', encoding="utf-8")
        script.chmod(0o755)
        self.created.append(str(script))
        self.log(f"Comando 'droidblocks' criado em {script}")
        if str(bin_dir) not in os.environ.get("PATH", ""):
            self.log(f"Dica: adicione {bin_dir} ao PATH para usar o comando no terminal.")

    def write_uninstaller(self, python):
        source = Path(__file__).resolve()
        dest = self.target / "uninstall.py"
        dest.write_text(
            "#!/usr/bin/env python3\n"
            '"""Desinstalador do DroidBlocks Studio (remove arquivos e atalhos criados)."""\n'
            "import runpy, sys\n"
            f"sys.argv = [{str(source.name)!r}, '--uninstall', '--dir', {str(self.target)!r}]\n"
            f"runpy.run_path({str(self.target / 'installer' / 'installer.py')!r}, run_name='__main__')\n",
            encoding="utf-8")
        self.log("Desinstalador criado: uninstall.py")

    def save_manifest(self):
        manifest = {"version": VERSION, "target": str(self.target), "created": self.created,
                    "system": SYSTEM}
        (self.target / MANIFEST_NAME).write_text(json.dumps(manifest, indent=2), encoding="utf-8")
        registry = registry_file()
        registry.parent.mkdir(parents=True, exist_ok=True)
        registry.write_text(json.dumps(manifest, indent=2), encoding="utf-8")


def registry_file():
    """Arquivo que lembra onde o app foi instalado (usado pela desinstalacao)."""
    from droidblocks.core.storage import config_dir
    return config_dir() / MANIFEST_NAME


def uninstall(target=None, log=print):
    manifest = None
    candidates = [Path(target) / MANIFEST_NAME] if target else []
    candidates.append(registry_file())
    for path in candidates:
        if path.exists():
            manifest = json.loads(path.read_text(encoding="utf-8"))
            break
    if manifest is None:
        log("Nenhuma instalacao encontrada.")
        return False
    for item in reversed(manifest["created"]):
        try:
            if item.startswith("registry:"):
                import winreg
                winreg.DeleteKey(winreg.HKEY_CURRENT_USER, item.split(":", 1)[1])
            else:
                path = Path(item)
                if path.is_symlink() or path.is_file():
                    path.unlink()
                elif path.is_dir():
                    shutil.rmtree(path, ignore_errors=True)
            log(f"Removido: {item}")
        except Exception as exc:
            log(f"Nao foi possivel remover {item}: {exc}")
    try:
        registry_file().unlink()
    except OSError:
        pass
    log("Desinstalacao concluida. Seus projetos (.dbp) e configuracoes foram mantidos.")
    return True


# ----------------------------------------------------------------- interface grafica

def gui():
    import tkinter as tk
    from tkinter import ttk, filedialog, messagebox
    from droidblocks.ui import theme
    from droidblocks.ui.theme import C, FONT

    root = tk.Tk()
    theme.setup(root)
    root.title(f"Instalar {APP_NAME}")
    theme.center_window(root, 640, 520)
    root.resizable(False, False)
    try:
        from droidblocks.core.png import render_icon
        icon = tk.PhotoImage(data=render_icon(64, "#2F81F7"))
        root.iconphoto(True, icon)
    except Exception:
        icon = None

    header = tk.Frame(root, bg=C["bg"])
    header.pack(fill="x")
    if icon:
        tk.Label(header, image=icon, bg=C["bg"]).pack(side="left", padx=20, pady=18)
    titles = tk.Frame(header, bg=C["bg"])
    titles.pack(side="left")
    tk.Label(titles, text=APP_NAME, bg=C["bg"], fg=C["text"], font=FONT["title"]).pack(anchor="w")
    tk.Label(titles, text=f"Versão {VERSION}  |  {SYSTEM}  |  Python {platform.python_version()}",
             bg=C["bg"], fg=C["muted"]).pack(anchor="w")

    body = ttk.Frame(root)
    body.pack(fill="both", expand=True, padx=20, pady=12)
    ttk.Label(body, text="Pasta de instalação").pack(anchor="w")
    row = ttk.Frame(body)
    row.pack(fill="x")
    target = tk.StringVar(value=str(default_install_dir()))
    ttk.Entry(row, textvariable=target).pack(side="left", fill="x", expand=True)
    ttk.Button(row, text="Alterar...", command=lambda: target.set(
        filedialog.askdirectory(initialdir=target.get()) or target.get())).pack(side="left", padx=4)
    desktop = tk.BooleanVar(value=True)
    menu = tk.BooleanVar(value=True)
    command = tk.BooleanVar(value=True)
    menu_label = {"Windows": "Atalho no Menu Iniciar", "Darwin": "Aplicativo em ~/Applications"}.get(
        SYSTEM, "Atalho no menu de aplicativos")
    ttk.Checkbutton(body, text="Atalho na área de trabalho", variable=desktop).pack(anchor="w", pady=(12, 0))
    ttk.Checkbutton(body, text=menu_label, variable=menu).pack(anchor="w")
    ttk.Checkbutton(body, text="Comando 'droidblocks' no terminal", variable=command).pack(anchor="w")
    log_box = tk.Text(body, height=9, bg=C["panel2"], fg=C["text"], relief="flat", font=FONT["small"],
                      highlightthickness=1, highlightbackground=C["border"])
    log_box.pack(fill="both", expand=True, pady=10)
    progress = ttk.Progressbar(body, mode="determinate")
    progress.pack(fill="x")

    def log(text):
        root.after(0, lambda: (log_box.insert("end", text + "\n"), log_box.see("end")))

    bar = ttk.Frame(root)
    bar.pack(fill="x", padx=20, pady=(0, 16))
    install_btn = ttk.Button(bar, text="Instalar", style="Accent.TButton")
    install_btn.pack(side="right")
    ttk.Button(bar, text="Cancelar", command=root.destroy).pack(side="right", padx=6)

    def uninstall_action():
        if messagebox.askyesno("Desinstalar", "Remover a instalação existente do DroidBlocks Studio?"):
            uninstall(log=log)

    ttk.Button(bar, text="Desinstalar", command=uninstall_action).pack(side="left")

    def finish(error, path):
        progress.stop()
        progress.configure(mode="determinate", value=0 if error else 100)
        install_btn.state(["!disabled"])
        if error:
            messagebox.showerror("Falha na instalação", str(error))
            return
        install_btn.configure(text="Abrir agora", command=lambda: (
            subprocess.Popen([str(python_gui_executable()), str(Path(path) / "main.py")], cwd=str(path)),
            root.destroy()))
        messagebox.showinfo("Pronto", f"{APP_NAME} foi instalado em:\n{path}")

    def start():
        install_btn.state(["disabled"])
        progress.configure(mode="indeterminate")
        progress.start(10)

        def work():
            try:
                path = Installer(target.get(), desktop.get(), menu.get(), command.get(), log).run()
                root.after(0, lambda: finish(None, path))
            except Exception as exc:
                root.after(0, lambda e=exc: finish(e, None))
        threading.Thread(target=work, daemon=True).start()

    install_btn.configure(command=start)
    log(f"Pronto para instalar a partir de {SOURCE}")
    root.mainloop()


def main():
    parser = argparse.ArgumentParser(description=f"Instalador do {APP_NAME}")
    parser.add_argument("--silent", action="store_true", help="instala sem interface grafica")
    parser.add_argument("--dir", help="pasta de instalacao")
    parser.add_argument("--no-desktop", action="store_true", help="nao cria atalho na area de trabalho")
    parser.add_argument("--no-menu", action="store_true", help="nao cria atalho no menu do sistema")
    parser.add_argument("--no-command", action="store_true", help="nao cria o comando de terminal")
    parser.add_argument("--uninstall", action="store_true", help="remove a instalacao")
    args = parser.parse_args()
    if args.uninstall:
        sys.exit(0 if uninstall(args.dir) else 1)
    if args.silent:
        try:
            Installer(args.dir or default_install_dir(), not args.no_desktop, not args.no_menu,
                      not args.no_command).run()
        except Exception as exc:
            print(f"Erro: {exc}")
            sys.exit(1)
        return
    gui()


if __name__ == "__main__":
    main()
