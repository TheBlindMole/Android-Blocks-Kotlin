"""Arquivos complementares: algoritmos, testes, documentacao e lista de requisitos."""

import datetime

from ...catalog.algorithms import ALGORITHMS
from ...catalog.libraries import LIBRARIES, PLUGINS
from ...catalog.features import PERMISSIONS
from ...catalog.components import COMPONENTS
from ... import __version__, APP_NAME


def algorithms(ctx):
    for key in ctx.resolved.algorithms:
        algo = ALGORITHMS[key]
        ctx.add_kotlin(f"algorithms/{algo.cls}.kt", f"package %PKG%.algorithms\n\n{algo.code}\n")


def tests(ctx):
    r = ctx.resolved
    ctx.add_kotlin("ExampleUnitTest.kt", '''package %PKG%

import %PKG%.data.model.ItemFilters
import %PKG%.data.model.ListItem
import %PKG%.data.model.asText
import org.junit.Assert.assertEquals
import org.junit.Test

/** Testes locais (rodam na JVM, sem emulador). */
class ExampleUnitTest {

    private val items = listOf(
        ListItem("1", "Pizza Margherita", "Italiana"),
        ListItem("2", "Sushi", "Japonesa"),
        ListItem("3", "Hamburguer", "Lanches")
    )

    @Test
    fun busca_filtra_por_titulo_e_subtitulo() {
        assertEquals(1, ItemFilters.apply(items, "pizza").size)
        assertEquals(1, ItemFilters.apply(items, "japonesa").size)
        assertEquals(3, ItemFilters.apply(items, "").size)
    }

    @Test
    fun filtro_de_chip_respeita_opcao_todos() {
        assertEquals(3, ItemFilters.apply(items, "", "Todos", "Todos").size)
        assertEquals(1, ItemFilters.apply(items, "", "Lanches", "Todos").size)
    }

    @Test
    fun asText_formata_valores() {
        assertEquals("10", 10.0.asText())
        assertEquals("a, b", listOf("a", "b").asText())
        assertEquals("", null.asText())
    }
}
''', "test")
    if r.algorithms:
        tests_code = []
        for key in r.algorithms:
            algo = ALGORITHMS[key]
            tests_code.append(f'''    @Test
    fun {key}() {{
        {algo.test}
    }}''')
        ctx.add_kotlin("algorithms/AlgorithmsTest.kt", f'''package %PKG%.algorithms

import org.junit.Assert.assertArrayEquals
import org.junit.Assert.assertEquals
import org.junit.Assert.assertFalse
import org.junit.Assert.assertNotEquals
import org.junit.Assert.assertTrue
import org.junit.Test

/** Testes dos algoritmos incluidos no projeto. */
class AlgorithmsTest {{

{(chr(10) + chr(10)).join(tests_code)}
}}
''', "test")
    if r.has("validators"):
        ctx.add_kotlin("features/ValidatorsTest.kt", '''package %PKG%.features

import org.junit.Assert.assertFalse
import org.junit.Assert.assertTrue
import org.junit.Test

/** Testes das regras de validacao de formularios. */
class ValidatorsTest {

    @Test
    fun email() {
        assertTrue(Validators.email("ana@exemplo.com"))
        assertFalse(Validators.email("ana@"))
    }

    @Test
    fun documentos() {
        assertTrue(Validators.cpf("529.982.247-25"))
        assertFalse(Validators.cpf("111.111.111-11"))
        assertTrue(Validators.cnpj("11.222.333/0001-81"))
        assertTrue(Validators.nif("123456789"))
    }

    @Test
    fun senha_forte() {
        assertTrue(Validators.strongPassword("Senha123"))
        assertFalse(Validators.strongPassword("senha"))
    }
}
''', "test")
    if ctx.compose:
        ui_test = '''package %PKG%

import androidx.compose.ui.test.junit4.createAndroidComposeRule
import androidx.compose.ui.test.onRoot
import androidx.compose.ui.test.assertIsDisplayed
import androidx.test.ext.junit.runners.AndroidJUnit4
import org.junit.Rule
import org.junit.Test
import org.junit.runner.RunWith

/** Teste instrumentado: abre o app e verifica se a interface foi desenhada. */
@RunWith(AndroidJUnit4::class)
class AppLaunchTest {

    @get:Rule
    val composeRule = createAndroidComposeRule<MainActivity>()

    @Test
    fun app_abre_e_exibe_a_tela_inicial() {
        composeRule.onRoot().assertIsDisplayed()
    }
}
'''
    else:
        start = ctx.project.get_start_screen()
        cls = ctx.screen_class(start)
        ui_test = f'''package %PKG%

import androidx.test.core.app.ActivityScenario
import androidx.test.espresso.Espresso.onView
import androidx.test.espresso.assertion.ViewAssertions.matches
import androidx.test.espresso.matcher.ViewMatchers.isDisplayed
import androidx.test.espresso.matcher.ViewMatchers.withId
import androidx.test.ext.junit.runners.AndroidJUnit4
import {ctx.screen_package(start)}.{cls}Activity
import org.junit.Test
import org.junit.runner.RunWith

/** Teste instrumentado: abre a tela inicial e verifica a barra superior. */
@RunWith(AndroidJUnit4::class)
class AppLaunchTest {{

    @Test
    fun tela_inicial_exibe_toolbar() {{
        ActivityScenario.launch({cls}Activity::class.java).use {{
            onView(withId(R.id.toolbar)).check(matches(isDisplayed()))
        }}
    }}
}}
'''
    if "ui_tests" in r.flags:
        ctx.add_kotlin("AppLaunchTest.kt", ui_test, "androidTest")
    ctx.add_kotlin("ExampleInstrumentedTest.kt", f'''package %PKG%

import androidx.test.ext.junit.runners.AndroidJUnit4
import androidx.test.platform.app.InstrumentationRegistry
import org.junit.Assert.assertEquals
import org.junit.Test
import org.junit.runner.RunWith

/** Teste instrumentado basico: confirma o pacote do aplicativo. */
@RunWith(AndroidJUnit4::class)
class ExampleInstrumentedTest {{

    @Test
    fun contexto_do_app() {{
        val context = InstrumentationRegistry.getInstrumentation().targetContext
        assertEquals("{ctx.pkg}", context.packageName)
    }}
}}
''', "androidTest")


def docs(ctx):
    p = ctx.project
    r = ctx.resolved
    v = ctx.versions
    ui = "Jetpack Compose (Material 3)" if ctx.compose else "Views XML com ViewBinding (Material 3)"
    nav = {"stack": "pilha de telas", "bottom": "barra inferior", "drawer": "menu lateral"}.get(p.navigation, p.navigation)
    screens = "\n".join(
        f"| {s.title or s.name} | `{ctx.screen_route(s)}` | {len([c for c in s.components if c.type in COMPONENTS])} | "
        f"{'sim' if s.in_nav else 'nao'} |" for s in p.screens)
    features = "\n".join(f"- **{f.name}** ({f.category}): {f.description}" for f in r.features) or "- Nenhuma"
    algos = "\n".join(f"- {ALGORITHMS[a].name}: `algorithms/{ALGORITHMS[a].cls}.kt`" for a in r.algorithms) or "- Nenhum"
    apis = "\n".join(f"- **{a.name}** ({a.base_url}): " + ", ".join(f"`{e.method} {e.path}`" for e in a.endpoints)
                     for a in p.apis) or "- Nenhuma"
    entities = "\n".join(f"- **{e.name}**: " + ", ".join(f"{f[0]} ({f[1]})" for f in e.fields) for e in p.entities) or "- Nenhuma"
    perms = "\n".join(f"- `{x}`" + (" (pedida ao usuario)" if PERMISSIONS.get(x, (False,))[0] else "") for x in r.permissions)
    notes = "\n".join(f"- {f.name}: {f.notes}" for f in r.features if f.notes) or "- Nenhuma configuracao externa necessaria."
    keys = []
    if "maps" in r.flags:
        keys.append("- `MAPS_API_KEY` em `local.properties` (Google Maps).")
    for api in p.apis:
        if api.auth == "api_key":
            keys.append(f"- `API_KEY_{api.name.upper()}` em `local.properties` (API {api.name}).")
    if any("google_services" in f.plugins for f in r.features):
        keys.append("- Arquivo `app/google-services.json` do console do Firebase.")
    keys_text = "\n".join(keys) or "- Nenhuma chave necessaria."
    ctx.add("README.md", f'''# {p.name}

{p.description or "Aplicativo Android gerado com o " + APP_NAME + "."}

- Pacote: `{p.package}`
- Interface: {ui}
- Navegacao: {nav}
- SDK minimo: {p.min_sdk} (Android {_android_name(p.min_sdk)}) | SDK alvo: {p.target_sdk}
- Linguagem: Kotlin {v["kotlin"]} | Android Gradle Plugin {v["agp"]} | Gradle {v["gradle"]}

## Como abrir

1. Instale o Android Studio (versao estavel atual) com o JDK 17 ou superior (ja incluso no Android Studio).
2. No Android Studio: **File > Open** e selecione esta pasta.
3. Aguarde a sincronizacao do Gradle (a primeira vez baixa as dependencias e exige internet).
4. Clique em **Run** para instalar no emulador ou no aparelho conectado.

Pela linha de comando (com o wrapper incluso):

```
./gradlew assembleDebug        # Linux e macOS
gradlew.bat assembleDebug      # Windows
```

O APK fica em `app/build/outputs/apk/debug/`.

## Chaves e arquivos externos

{keys_text}

Copie `local.properties.example` para `local.properties` e preencha os valores.

## Telas

| Tela | Rota | Blocos | No menu |
|------|------|--------|---------|
{screens}

## Funcionalidades incluidas

{features}

## Algoritmos

{algos}

## APIs

{apis}

## Banco de dados local (Room)

{entities}

## Permissoes

{perms}

## Observacoes

{notes}

## Estrutura

```
app/src/main/java/{ctx.pkg_path}/
  App.kt                 Classe Application e inicializacoes globais
  di/                    Container de dependencias
  data/model/            ListItem e conversores
  data/local/            Entidades, DAOs e banco Room
  data/remote/           Modelos, servicos Retrofit e NetworkModule
  data/repository/       Repositorio unico usado pelas telas
  features/              Funcionalidades adicionadas pelo construtor
  algorithms/            Algoritmos selecionados
  navigation/            Rotas e navegacao
  ui/                    Telas, ViewModels, componentes e tema
  util/                  Intents, permissoes e extensoes
```

Gerado pelo {APP_NAME} {__version__} em {datetime.date.today().isoformat()}.
O arquivo `droidblocks-project.dbp` permite reabrir este projeto no construtor.
''')

    # REQUIREMENTS.md e requirements.txt
    libs = []
    for key in r.libs:
        lib = LIBRARIES[key]
        version = v[lib.version] if lib.version else f"(gerenciada pela BOM {LIBRARIES[lib.bom].module})"
        libs.append((lib.module, version, lib.conf))
    lib_rows = "\n".join(f"| `{m}` | {ver} | {conf} |" for m, ver, conf in libs)
    plugin_rows = "\n".join(f"| `{PLUGINS[k].plugin_id}` | {v[PLUGINS[k].version]} |" for k in r.plugins)
    ctx.add("REQUIREMENTS.md", f'''# Requisitos do projeto {p.name}

## Ambiente de desenvolvimento

| Item | Versao |
|------|--------|
| Android Studio | Ladybug (2024.2) ou mais recente |
| JDK | 17 ou superior (o Android Studio ja inclui) |
| Gradle | {v["gradle"]} (baixado automaticamente pelo wrapper) |
| Android Gradle Plugin | {v["agp"]} |
| Kotlin | {v["kotlin"]} |
| Android SDK Platform | API {p.compile_sdk} |
| Android SDK Build-Tools | 34.0.0 ou superior |
| Aparelho/emulador | Android {_android_name(p.min_sdk)} (API {p.min_sdk}) ou superior |

## Plugins Gradle

| Plugin | Versao |
|--------|--------|
{plugin_rows}

## Bibliotecas

| Modulo | Versao | Configuracao |
|--------|--------|--------------|
{lib_rows}

## Permissoes do Android

{perms}

## Chaves e arquivos externos

{keys_text}
''')
    req = [f"# Dependencias do projeto {p.name} (formato grupo:artefato:versao).",
           "# Referencia apenas: o Gradle le as versoes de gradle/libs.versions.toml.", ""]
    for m, ver, conf in libs:
        version = ver if not ver.startswith("(") else "bom"
        req.append(f"{m}:{version}    # {conf}")
    req += ["", "# Plugins"] + [f"{PLUGINS[k].plugin_id}:{v[PLUGINS[k].version]}" for k in r.plugins]
    ctx.add("requirements.txt", "\n".join(req))


def _android_name(api):
    names = {21: "5.0", 22: "5.1", 23: "6.0", 24: "7.0", 25: "7.1", 26: "8.0", 27: "8.1", 28: "9", 29: "10",
             30: "11", 31: "12", 32: "12L", 33: "13", 34: "14", 35: "15", 36: "16"}
    return names.get(int(api), str(api))
