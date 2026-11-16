"""Integracao opcional com as ferramentas Android instaladas no computador.

Localiza o Android Studio, o JDK e o Android SDK, abre o projeto gerado no
Android Studio e compila o APK de depuracao chamando o Gradle Wrapper.
Nada aqui e obrigatorio: o DroidBlocks funciona sem estas ferramentas.
"""

import os
import shutil
import subprocess
import sys
from pathlib import Path

HOME = Path.home()
IS_WIN = sys.platform.startswith("win")
IS_MAC = sys.platform == "darwin"


def _first_existing(paths):
    for path in paths:
        if path and Path(path).exists():
            return Path(path)
    return None


def _program_files():
    return [os.environ.get(k) for k in ("ProgramFiles", "ProgramW6432", "ProgramFiles(x86)") if os.environ.get(k)]


def studio_dirs():
    """Pastas comuns de instalacao do Android Studio neste sistema."""
    if IS_WIN:
        local = os.environ.get("LOCALAPPDATA", "")
        dirs = [Path(p) / "Android" / "Android Studio" for p in _program_files()]
        if local:
            dirs.append(Path(local) / "Programs" / "Android Studio")
        return dirs
    if IS_MAC:
        return [Path("/Applications/Android Studio.app"), HOME / "Applications" / "Android Studio.app"]
    return [Path("/opt/android-studio"), HOME / "android-studio", Path("/usr/local/android-studio"),
            Path("/snap/android-studio/current"), HOME / ".local" / "share" / "JetBrains" / "Toolbox" / "apps" / "android-studio"]


def find_studio():
    """Executavel (ou pacote .app no macOS) do Android Studio, ou None."""
    for directory in studio_dirs():
        if IS_MAC and directory.exists():
            return directory
        candidate = directory / "bin" / ("studio64.exe" if IS_WIN else "studio.sh")
        if candidate.exists():
            return candidate
    for name in ("android-studio", "studio", "studio.sh"):
        found = shutil.which(name)
        if found:
            return Path(found)
    return None


def find_sdk():
    """Pasta do Android SDK, ou None."""
    for key in ("ANDROID_HOME", "ANDROID_SDK_ROOT"):
        value = os.environ.get(key)
        if value and Path(value).exists():
            return Path(value)
    if IS_WIN:
        local = os.environ.get("LOCALAPPDATA", "")
        candidates = [Path(local) / "Android" / "Sdk"] if local else []
    elif IS_MAC:
        candidates = [HOME / "Library" / "Android" / "sdk"]
    else:
        candidates = [HOME / "Android" / "Sdk", HOME / "Android" / "sdk", Path("/opt/android-sdk")]
    return _first_existing(candidates)


def _java_in(home):
    exe = Path(home) / "bin" / ("java.exe" if IS_WIN else "java")
    return exe.exists()


def find_java_home():
    """JDK para o Gradle: JAVA_HOME, o JBR do Android Studio ou o java do PATH."""
    value = os.environ.get("JAVA_HOME")
    if value and _java_in(value):
        return Path(value)
    for directory in studio_dirs():
        for sub in (("Contents", "jbr", "Contents", "Home"), ("jbr",), ("jre",)):
            home = directory.joinpath(*sub)
            if _java_in(home):
                return home
    java = shutil.which("java")
    if java:
        # .../bin/java -> pasta do JDK (resolve links simbolicos como /usr/bin/java).
        return Path(java).resolve().parent.parent
    return None


def environment_report():
    """Lista legivel do que foi encontrado, para mostrar ao usuario."""
    studio, sdk, java = find_studio(), find_sdk(), find_java_home()
    return [
        ("Android Studio", str(studio) if studio else "nao encontrado"),
        ("Android SDK", str(sdk) if sdk else "nao encontrado (defina ANDROID_HOME)"),
        ("JDK", str(java) if java else "nao encontrado (instale o JDK 17 ou o Android Studio)"),
    ]


def open_in_studio(project_dir):
    """Abre a pasta do projeto no Android Studio. Retorna False se ele nao foi encontrado."""
    studio = find_studio()
    if studio is None:
        return False
    try:
        if IS_MAC:
            subprocess.Popen(["open", "-a", str(studio), str(project_dir)])
        else:
            subprocess.Popen([str(studio), str(project_dir)], cwd=str(project_dir))
        return True
    except OSError:
        return False


def write_local_properties(project_dir, sdk):
    """Grava sdk.dir no local.properties preservando as outras linhas (ex.: chaves de API)."""
    path = Path(project_dir) / "local.properties"
    escaped = str(sdk).replace("\\", "\\\\").replace(":", "\\:")
    lines = []
    if path.exists():
        lines = [line for line in path.read_text(encoding="utf-8").splitlines() if not line.startswith("sdk.dir=")]
    lines.insert(0, f"sdk.dir={escaped}")
    path.write_text("\n".join(lines) + "\n", encoding="utf-8")


def apk_path(project_dir):
    return Path(project_dir) / "app" / "build" / "outputs" / "apk" / "debug" / "app-debug.apk"


def start_build(project_dir, task="assembleDebug"):
    """Inicia o Gradle Wrapper e devolve o processo (saida combinada em texto).

    Lanca RuntimeError com uma mensagem clara quando falta SDK ou JDK.
    """
    project_dir = Path(project_dir)
    sdk = find_sdk()
    if sdk is None:
        raise RuntimeError("Android SDK nao encontrado. Instale o Android Studio ou defina a variavel ANDROID_HOME.")
    java_home = find_java_home()
    if java_home is None:
        raise RuntimeError("JDK nao encontrado. Instale o Android Studio (que inclui o JDK) ou o JDK 17.")
    write_local_properties(project_dir, sdk)
    wrapper = project_dir / ("gradlew.bat" if IS_WIN else "gradlew")
    if not wrapper.exists():
        raise RuntimeError("Gradle Wrapper nao encontrado na pasta do projeto.")
    if not IS_WIN:
        wrapper.chmod(wrapper.stat().st_mode | 0o111)
    env = dict(os.environ, JAVA_HOME=str(java_home), ANDROID_HOME=str(sdk))
    command = [str(wrapper), task, "--console=plain"]
    flags = getattr(subprocess, "CREATE_NO_WINDOW", 0) if IS_WIN else 0
    return subprocess.Popen(command, cwd=str(project_dir), env=env, stdout=subprocess.PIPE,
                            stderr=subprocess.STDOUT, text=True, encoding="utf-8", errors="replace",
                            bufsize=1, creationflags=flags)
