"""Validacao estatica dos projetos gerados (sem Android SDK).

Verifica, para todos os modelos e nos dois modos de interface:
- XML bem formado;
- recursos referenciados (@string, @drawable, @layout, @menu, @color, @xml, @mipmap) existem;
- R.<tipo>.<nome> usados no Kotlin existem;
- campos de ViewBinding usados existem no layout correspondente;
- Routes.X usados existem;
- funcoes viewModel.<nome> chamadas existem no ViewModel da tela.

Uso: python tests/validate_generated.py
"""

import re
import sys
import xml.dom.minidom
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from droidblocks.catalog import templates  # noqa: E402
from droidblocks.core.generator import generate  # noqa: E402
from droidblocks.catalog.components import (COMPONENT_LIST, ACTION_LIST, LIST_COMPONENTS,  # noqa: E402
                                            default_props, join_actions)
from droidblocks.catalog.features import ALL_FEATURES  # noqa: E402
from droidblocks.core.model import Component, Screen  # noqa: E402


def camel(view_id):
    parts = view_id.split("_")
    return parts[0] + "".join(p[:1].upper() + p[1:] for p in parts[1:])


def check(result):
    problems = []
    files = result.files
    res = {}
    ids_by_layout = {}
    all_ids = set()
    for path, content in files.items():
        if path.endswith(".xml") and isinstance(content, str):
            try:
                xml.dom.minidom.parseString(content.encode("utf-8"))
            except Exception as exc:
                problems.append(f"XML invalido {path}: {exc}")
        m = re.match(r"app/src/main/res/([a-z]+)(?:-[\w-]+)?/([\w.]+)$", path)
        if m:
            kind, name = m.group(1), m.group(2).rsplit(".", 1)[0]
            res.setdefault(kind, set()).add(name)
            if isinstance(content, str):
                ids = set(re.findall(r'@\+id/(\w+)', content))
                all_ids |= ids
                if kind == "layout":
                    ids_by_layout[name] = ids
                if path.endswith("strings.xml"):
                    res.setdefault("string", set()).update(re.findall(r'<string name="(\w+)"', content))
                if path.endswith("colors.xml"):
                    res.setdefault("color", set()).update(re.findall(r'<color name="(\w+)"', content))
                if path.endswith("themes.xml"):
                    res.setdefault("style", set()).update(re.findall(r'<style name="([\w.]+)"', content))
    for path, content in files.items():
        if not isinstance(content, str):
            continue
        if path.endswith(".xml"):
            for kind, name in re.findall(r"@(string|drawable|layout|menu|color|xml|mipmap|style)/([\w.]+)", content):
                if kind == "style" and (name.startswith("Widget.") or name.startswith("Theme.App")):
                    if name.startswith("Theme.App") and name not in res.get("style", set()):
                        problems.append(f"{path}: estilo inexistente @{kind}/{name}")
                    continue
                if name not in res.get(kind, set()):
                    problems.append(f"{path}: recurso inexistente @{kind}/{name}")
        if path.endswith(".kt"):
            for kind, name in re.findall(r"(?<!android\.)\bR\.(string|drawable|layout|id|menu|color|xml|mipmap)\.(\w+)", content):
                pool = all_ids if kind == "id" else res.get(kind, set())
                if name not in pool:
                    problems.append(f"{path}: R.{kind}.{name} inexistente")
            layout = re.search(r"(\w+)Binding\.inflate", content)
            if layout:
                lname = re.sub(r"(?<!^)([A-Z])", r"_\1", layout.group(1)).lower()
                fields = {camel(i) for i in ids_by_layout.get(lname, set())}
                for field in set(re.findall(r"\bbinding\.(\w+)", content)):
                    if field not in fields and field != "root":
                        problems.append(f"{path}: binding.{field} nao existe em {lname}.xml")
    routes_file = next((c for p, c in files.items() if p.endswith(("navigation/AppNavigation.kt", "navigation/Navigator.kt"))), "")
    routes = set(re.findall(r"const val (\w+) =", routes_file))
    for path, content in files.items():
        if path.endswith(".kt") and isinstance(content, str):
            for name in re.findall(r"\bRoutes\.(\w+)", content):
                if name not in routes:
                    problems.append(f"{path}: Routes.{name} inexistente")
            if path.endswith(("Screen.kt", "Activity.kt")):
                vm_path = re.sub(r"(Screen|Activity)\.kt$", "ViewModel.kt", path)
                vm = files.get(vm_path, "")
                if vm:
                    defined = set(re.findall(r"fun (\w+)\(", vm)) | {"uiState", "messages"}
                    for call in set(re.findall(r"viewModel(?:::|\.)(\w+)", content)):
                        if call not in defined:
                            problems.append(f"{path}: viewModel.{call} nao existe")
    return problems


def kitchen_sink(mode):
    """Projeto com todos os blocos, todas as acoes (inclusive encadeadas) e todas as funcionalidades."""
    project = templates.build_project(templates.find("Loja online"), "Tudo", "com.validacao.tudo")
    project.ui_mode = mode
    target = project.screens[1].name
    screen = Screen(name="Tudo", title="Tudo")
    for comp in COMPONENT_LIST:
        props = default_props(comp.type)
        if comp.type in LIST_COMPONENTS:
            props["source"] = "sample:products"
            props["item_action"] = join_actions([a.key for a in ACTION_LIST if a.needs_item] + [f"navigate:{target}"])
        screen.components.append(Component(type=comp.type, props=props))
    for action in ACTION_LIST:
        if action.needs_item or action.key == "none":
            continue
        arg = {"screen": target, "text": "teste", "url": "https://example.com"}.get(action.arg, "")
        value = f"{action.key}:{arg}" if arg else action.key
        screen.components.append(Component(type="button", props={"text": action.key, "action": value}))
    chain = join_actions(["toast:um", "vibrate", "pick_file", f"navigate:{target}"])
    screen.components.append(Component(type="button", props={"text": "cadeia", "action": chain}))
    project.screens.append(screen)
    project.features = [f.key for f in ALL_FEATURES if not f.builtin]
    return project


def main():
    total = 0
    for mode in ("compose", "views"):
        result = generate(kitchen_sink(mode), preview=True)
        problems = check(result)
        total += len(problems)
        for problem in problems[:20]:
            print(f"[{mode}] Tudo: {problem}")
    for mode in ("compose", "views"):
        for index, tpl in enumerate(templates.TEMPLATES):
            project = templates.build_project(tpl, package=f"com.validacao.t{index}")
            project.ui_mode = mode
            result = generate(project, preview=True)
            problems = check(result)
            total += len(problems)
            for problem in problems[:8]:
                print(f"[{mode}] {tpl['name']}: {problem}")
    print(f"Concluido: {total} problemas em {len(templates.TEMPLATES) * 2 + 2} projetos.")
    return 1 if total else 0


if __name__ == "__main__":
    sys.exit(main())
