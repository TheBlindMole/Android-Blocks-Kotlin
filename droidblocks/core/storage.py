"""Salvamento de projetos (.dbp) e configuracoes do usuario."""

import json
import os
import platform
from pathlib import Path

from .model import Project

PROJECT_EXT = ".dbp"


def config_dir():
    """Pasta de configuracao conforme o sistema operacional."""
    if os.name == "nt":
        base = Path(os.environ.get("APPDATA") or Path.home() / "AppData" / "Roaming")
        return base / "DroidBlocks"
    if platform.system() == "Darwin":
        return Path.home() / "Library" / "Application Support" / "DroidBlocks"
    return Path(os.environ.get("XDG_CONFIG_HOME") or Path.home() / ".config") / "droidblocks"


def default_output_dir():
    docs = Path.home() / "Documents"
    if not docs.exists():
        docs = Path.home()
    return docs / "DroidBlocksProjects"


def save_project(project, path):
    path = Path(path)
    if path.suffix != PROJECT_EXT:
        path = path.with_suffix(PROJECT_EXT)
    path.parent.mkdir(parents=True, exist_ok=True)
    tmp = path.with_suffix(".tmp")
    tmp.write_text(json.dumps(project.to_dict(), ensure_ascii=False, indent=2), encoding="utf-8")
    tmp.replace(path)
    return path


def load_project(path):
    data = json.loads(Path(path).read_text(encoding="utf-8"))
    return Project.from_dict(data)


class Settings:
    """Preferencias persistentes: projetos recentes, pasta de saida e versoes."""

    def __init__(self):
        self.path = config_dir() / "settings.json"
        self.data = {"recent": [], "output_dir": str(default_output_dir()), "versions": {},
                     "autosave": True, "open_folder_after_generate": True}
        try:
            if self.path.exists():
                self.data.update(json.loads(self.path.read_text(encoding="utf-8")))
        except (OSError, ValueError):
            pass

    def save(self):
        try:
            self.path.parent.mkdir(parents=True, exist_ok=True)
            self.path.write_text(json.dumps(self.data, ensure_ascii=False, indent=2), encoding="utf-8")
        except OSError:
            pass

    def add_recent(self, path):
        path = str(path)
        recent = [p for p in self.data.get("recent", []) if p != path]
        recent.insert(0, path)
        self.data["recent"] = recent[:10]
        self.save()

    def recent(self):
        return [p for p in self.data.get("recent", []) if Path(p).exists()]

    def __getitem__(self, key):
        return self.data.get(key)

    def __setitem__(self, key, value):
        self.data[key] = value
        self.save()
