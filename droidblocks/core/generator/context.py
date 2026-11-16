"""Contexto compartilhado durante a geracao de um projeto."""

import re

from ...catalog.libraries import DEFAULT_VERSIONS
from ...catalog.components import COMPONENTS
from ..naming import to_pascal, to_snake, android_string


class GenContext:
    """Guarda o projeto, o resultado do resolvedor e os arquivos gerados."""

    def __init__(self, project, resolved, versions=None):
        self.project = project
        self.resolved = resolved
        self.pkg = project.package
        self.pkg_path = project.package.replace(".", "/")
        self.compose = project.ui_mode == "compose"
        self.versions = dict(DEFAULT_VERSIONS)
        self.versions.update(versions or {})
        self.versions.update(project.versions or {})
        self.files = {}
        self.strings = {}
        self._string_by_text = {}
        self.feature_symbols = set()

    # ----- arquivos -----

    def add(self, path, content):
        """Adiciona um arquivo relativo a raiz do projeto Android."""
        if isinstance(content, str):
            content = content.rstrip("\n") + "\n"
        self.files[path] = content

    def add_kotlin(self, rel_path, content, source_set="main"):
        """Adiciona um arquivo Kotlin relativo ao pacote do app."""
        content = content.replace("%PKG%", self.pkg)
        self.add(f"app/src/{source_set}/java/{self.pkg_path}/{rel_path}", content)

    def add_res(self, rel_path, content):
        self.add(f"app/src/main/res/{rel_path}", content)

    def has_feature_files(self):
        prefix = f"app/src/main/java/{self.pkg_path}/features/"
        return any(p.startswith(prefix) for p in self.files)

    # ----- strings.xml -----

    def string(self, hint, text):
        """Registra um texto em strings.xml e devolve o nome do recurso."""
        text = "" if text is None else str(text)
        if text in self._string_by_text:
            return self._string_by_text[text]
        base = to_snake(hint, "text")[:48].strip("_") or "text"
        name = base
        index = 2
        while name in self.strings:
            name = f"{base}_{index}"
            index += 1
        self.strings[name] = text
        self._string_by_text[text] = name
        return name

    def strings_xml(self, comment=None):
        lines = ['<?xml version="1.0" encoding="utf-8"?>']
        if comment:
            lines.append(f"<!-- {comment} -->")
        lines.append("<resources>")
        for name, text in self.strings.items():
            extra = ' formatted="false"' if "%" in text else ""
            lines.append(f'    <string name="{name}"{extra}>{android_string(text)}</string>')
        lines.append("</resources>")
        return "\n".join(lines)

    # ----- utilidades -----

    def screen_class(self, screen):
        return to_pascal(screen.name, "Screen")

    def screen_route(self, screen):
        return to_snake(screen.name, "screen")

    def screen_package(self, screen):
        return f"{self.pkg}.ui.screens.{to_snake(screen.name, 'screen').replace('_', '')}"

    def screen_dir(self, screen):
        return f"ui/screens/{to_snake(screen.name, 'screen').replace('_', '')}"

    def valid_components(self, screen):
        return [c for c in screen.components if c.type in COMPONENTS]

    def route_const(self, screen_name):
        return to_snake(screen_name, "screen").upper()


def collect_imports(body, import_map, extra=()):
    """Seleciona os imports cujo simbolo aparece no corpo do arquivo."""
    found = set(extra)
    # Ignora comentarios para nao importar simbolos citados apenas em textos de documentacao.
    body = re.sub(r"/\*.*?\*/", "", body, flags=re.S)
    body = re.sub(r"(?m)^\s*//.*$", "", body)
    for symbol, imp in import_map.items():
        if symbol.startswith("."):
            # Funcoes de extensao: aparecem depois de um ponto (ex.: 16.dp, Modifier.padding).
            pattern = re.escape(symbol) + r"\b"
        else:
            pattern = r"(?<![\w.])" + re.escape(symbol) + r"\b"
        if re.search(pattern, body):
            if isinstance(imp, (list, tuple)):
                found.update(imp)
            else:
                found.add(imp)
    if re.search(r"\bby\b", body):
        found.add("androidx.compose.runtime.getValue")
        if re.search(r"\bvar\s+\w+\s+by\b", body):
            found.add("androidx.compose.runtime.setValue")
    return sorted(found)
