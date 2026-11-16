"""Testes do gerador: todos os modelos, nos dois modos de interface, geram projetos completos.

Uso: python tests/test_generator.py
"""

import sys
import unittest
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from droidblocks.catalog import templates  # noqa: E402
from droidblocks.catalog.features import FEATURES  # noqa: E402
from droidblocks.catalog.algorithms import ALGORITHMS  # noqa: E402
from droidblocks.core.generator import generate  # noqa: E402
from droidblocks.core.model import Project  # noqa: E402
from droidblocks.core.resolver import auto_organize  # noqa: E402
from droidblocks.core import json_infer  # noqa: E402

REQUIRED = ["settings.gradle.kts", "build.gradle.kts", "app/build.gradle.kts", "gradle/libs.versions.toml",
            "gradle/wrapper/gradle-wrapper.properties", "app/src/main/AndroidManifest.xml", "README.md",
            "REQUIREMENTS.md", "requirements.txt", "app/src/main/res/values/strings.xml"]


class GeneratorTest(unittest.TestCase):

    def test_todos_os_modelos(self):
        self.assertGreaterEqual(len(templates.TEMPLATES), 100)
        for mode in ("compose", "views"):
            for index, tpl in enumerate(templates.TEMPLATES):
                project = templates.build_project(tpl, package=f"com.teste.t{index}")
                project.ui_mode = mode
                result = generate(project, preview=True)
                self.assertFalse(result.resolved.errors, f"{tpl['name']}: {result.resolved.errors}")
                for path in REQUIRED:
                    self.assertIn(path, result.files, f"{tpl['name']} ({mode}) sem {path}")
                for path, content in result.files.items():
                    if path.endswith(".kt"):
                        self.assertNotIn("%PKG%", content, path)
                        self.assertEqual(content.count("{"), content.count("}"), f"chaves desbalanceadas em {path}")

    def test_todas_funcionalidades_e_algoritmos(self):
        project = templates.build_project(templates.find("Onboarding + app base"), package="com.teste.tudo")
        project.features = list(FEATURES)
        project.algorithms = list(ALGORITHMS)
        for mode in ("compose", "views"):
            project.ui_mode = mode
            result = generate(project, preview=True)
            self.assertFalse(result.resolved.errors)
            self.assertIn("app/src/test/java/com/teste/tudo/algorithms/AlgorithmsTest.kt", result.files)

    def test_organizar_cria_telas_faltantes(self):
        project = Project(name="Teste", package="com.teste.org")
        from droidblocks.catalog.templates import S, C
        project.screens = [S("Inicio", "Inicio", [C("button", action="navigate:Perfil")])]
        auto_organize(project)
        self.assertIsNotNone(project.screen_by_name("Perfil"))

    def test_acoes_encadeadas_e_novos_blocos(self):
        from droidblocks.catalog.templates import S, C
        from droidblocks.catalog.components import split_actions, join_actions
        self.assertEqual(split_actions("toast:a && vibrate"), ["toast:a", "vibrate"])
        self.assertEqual(join_actions(["toast:a", "none", "vibrate"]), "toast:a && vibrate")
        for mode in ("compose", "views"):
            project = Project(name="Cadeia", package="com.teste.cadeia")
            project.ui_mode = mode
            project.screens = [
                S("Inicio", "Inicio", [C("carousel", source="sample:default", item_action="navigate:Fim"),
                                      C("signature"), C("steps"), C("price_tag", old_value="R$ 10"),
                                      C("button", action="toast:um && vibrate && navigate:Fim")], nav=True),
                S("Fim", "Fim", [C("text", text="fim")]),
            ]
            for comp in project.screens[0].components:
                comp.id = f"c{id(comp)}"
            project.start_screen = "Inicio"
            files = generate(project, preview=True).files
            code = "\n".join(v for k, v in files.items() if k.endswith(".kt"))
            self.assertIn("navigate", code.lower())
            self.assertIn("vibrat", code.lower())
            if mode == "compose":
                self.assertIn("SignaturePad(", code)
                self.assertIn("LazyRow", code)
            else:
                self.assertIn("SignatureView", code)
                self.assertIn("LinearLayoutManager.HORIZONTAL", code)

    def test_inferencia_json(self):
        models, name, is_list, wrapper = json_infer.infer('{"products": [{"id": 1, "title": "a", "price": 2.5}], "total": 1}', "Page")
        self.assertEqual(wrapper, "products")
        self.assertFalse(is_list)
        self.assertEqual(len(models), 2)


if __name__ == "__main__":
    unittest.main(verbosity=2)
