"""Gerador de projetos Android Studio a partir de um Project do DroidBlocks.

Uso:
    result = generate(project)
    root = write_project(result, "/caminho/de/saida")
"""

import json
import stat
import zipfile
from dataclasses import dataclass
from pathlib import Path

from ..resolver import resolve
from ..naming import to_pascal
from .context import GenContext
from . import gradle, manifest, resources, data_gen, compose_gen, views_gen, extras

ASSETS = Path(__file__).resolve().parent.parent.parent / "assets"


@dataclass
class GenerationResult:
    project: object
    resolved: object
    files: dict

    @property
    def folder_name(self):
        return to_pascal(self.project.name, "MeuApp")

    def kotlin_files(self):
        return {k: v for k, v in self.files.items() if k.endswith(".kt")}


def generate(project, versions=None, preview=False):
    """Gera todos os arquivos do projeto em memoria (caminho relativo -> conteudo).

    Com preview=True os icones PNG nao sao desenhados (mais rapido, usado na pre-visualizacao).
    """
    resolved = resolve(project)
    ctx = GenContext(project, resolved, versions)
    ctx.preview = preview

    # 1. Arquivos das funcionalidades (antes das telas, que importam features.*)
    for feature in resolved.features:
        files = dict(feature.files)
        files.update(feature.files_compose if ctx.compose else feature.files_views)
        for path, code in files.items():
            ctx.add_kotlin(path, code)
    extras.algorithms(ctx)

    # 2. Build, manifesto e recursos
    gradle.generate(ctx)
    manifest.generate(ctx)
    resources.generate(ctx)

    # 3. Dados, interface e classe Application
    data_gen.generate(ctx)
    if ctx.compose:
        compose_gen.generate(ctx)
    else:
        views_gen.generate(ctx)
    data_gen.finish_app(ctx)

    # 4. Testes, documentacao, textos e wrapper do Gradle
    extras.tests(ctx)
    extras.docs(ctx)
    resources.write_strings(ctx)
    _wrapper(ctx)
    ctx.add("droidblocks-project.dbp", json.dumps(project.to_dict(), ensure_ascii=False, indent=2))
    return GenerationResult(project, resolved, dict(sorted(ctx.files.items())))


def _wrapper(ctx):
    folder = ASSETS / "gradle-wrapper"
    if not folder.exists():
        return
    for name, target in (("gradlew", "gradlew"), ("gradlew.bat", "gradlew.bat"),
                         ("gradle-wrapper.jar", "gradle/wrapper/gradle-wrapper.jar")):
        source = folder / name
        if source.exists():
            data = source.read_bytes()
            if name == "gradlew.bat":
                data = data.replace(b"\r\n", b"\n").replace(b"\n", b"\r\n")
            ctx.files[target] = data


def write_project(result, output_dir, overwrite=True):
    """Grava os arquivos em output_dir/<NomeDoProjeto> e devolve o caminho da pasta."""
    root = Path(output_dir) / result.folder_name
    if root.exists() and not overwrite:
        raise FileExistsError(f"A pasta {root} ja existe.")
    for rel, content in result.files.items():
        path = root / rel
        path.parent.mkdir(parents=True, exist_ok=True)
        if isinstance(content, bytes):
            path.write_bytes(content)
        else:
            path.write_text(content, encoding="utf-8", newline="\n")
    gradlew = root / "gradlew"
    if gradlew.exists():
        gradlew.chmod(gradlew.stat().st_mode | stat.S_IXUSR | stat.S_IXGRP | stat.S_IXOTH)
    return root


def zip_project(result, zip_path):
    """Compacta o projeto gerado em um arquivo .zip."""
    zip_path = Path(zip_path)
    zip_path.parent.mkdir(parents=True, exist_ok=True)
    with zipfile.ZipFile(zip_path, "w", zipfile.ZIP_DEFLATED) as archive:
        for rel, content in result.files.items():
            name = f"{result.folder_name}/{rel}"
            info = zipfile.ZipInfo(name)
            info.compress_type = zipfile.ZIP_DEFLATED
            info.external_attr = (0o755 if rel == "gradlew" else 0o644) << 16
            archive.writestr(info, content if isinstance(content, bytes) else content.encode("utf-8"))
    return zip_path


__all__ = ["generate", "write_project", "zip_project", "GenerationResult"]
