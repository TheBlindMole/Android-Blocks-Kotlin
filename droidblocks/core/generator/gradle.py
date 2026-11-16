"""Geracao dos arquivos Gradle (Kotlin DSL) e do catalogo de versoes."""

from ...catalog.libraries import LIBRARIES, PLUGINS, accessor
from ..naming import to_snake

CONF_ORDER = ["impl", "ksp", "debug", "test", "androidTest"]
CONF_NAME = {"impl": "implementation", "ksp": "ksp", "debug": "debugImplementation",
             "test": "testImplementation", "androidTest": "androidTestImplementation"}


def generate(ctx):
    p = ctx.project
    r = ctx.resolved
    v = ctx.versions

    # ----- libs.versions.toml -----
    used_versions = set()
    for key in r.libs:
        if LIBRARIES[key].version:
            used_versions.add(LIBRARIES[key].version)
    for key in r.plugins:
        used_versions.add(PLUGINS[key].version)
    toml = ["# Catalogo de versoes gerado pelo DroidBlocks.",
            "# Altere as versoes aqui para atualizar todo o projeto.", "", "[versions]"]
    for name in sorted(used_versions):
        toml.append(f'{name} = "{v[name]}"')
    toml += ["", "[libraries]"]
    for key in r.libs:
        lib = LIBRARIES[key]
        group, artifact = lib.module.split(":")
        if lib.version:
            toml.append(f'{lib.alias} = {{ group = "{group}", name = "{artifact}", version.ref = "{lib.version}" }}')
        else:
            toml.append(f'{lib.alias} = {{ group = "{group}", name = "{artifact}" }}')
    toml += ["", "[plugins]"]
    for key in r.plugins:
        plugin = PLUGINS[key]
        toml.append(f'{plugin.alias} = {{ id = "{plugin.plugin_id}", version.ref = "{plugin.version}" }}')
    ctx.add("gradle/libs.versions.toml", "\n".join(toml))

    # ----- settings.gradle.kts -----
    ctx.add("settings.gradle.kts", f'''// Configuracao dos repositorios e modulos do projeto.
pluginManagement {{
    repositories {{
        google {{
            content {{
                includeGroupByRegex("com\\\\.android.*")
                includeGroupByRegex("com\\\\.google.*")
                includeGroupByRegex("androidx.*")
            }}
        }}
        mavenCentral()
        gradlePluginPortal()
    }}
}}

dependencyResolutionManagement {{
    repositoriesMode.set(RepositoriesMode.FAIL_ON_PROJECT_REPOS)
    repositories {{
        google()
        mavenCentral()
    }}
}}

rootProject.name = "{p.name}"
include(":app")''')

    # ----- build.gradle.kts (raiz) -----
    root = ["// Arquivo de build da raiz: apenas declara os plugins usados pelos modulos.", "plugins {"]
    for key in r.plugins:
        root.append(f"    alias(libs.plugins.{PLUGINS[key].alias.replace('-', '.')}) apply false")
    root.append("}")
    ctx.add("build.gradle.kts", "\n".join(root))

    # ----- app/build.gradle.kts -----
    plugins = "\n".join(f"    alias(libs.plugins.{PLUGINS[k].alias.replace('-', '.')})" for k in r.plugins)
    build_features = ["        buildConfig = true"]
    if ctx.compose:
        build_features.insert(0, "        compose = true")
    else:
        build_features.insert(0, "        viewBinding = true")

    props_lines = []
    needs_local = "maps" in r.flags or any(api.auth == "api_key" for api in p.apis)
    if needs_local:
        props_lines.append('''// Le chaves privadas do arquivo local.properties (que nao vai para o Git).
val localProperties = java.util.Properties().apply {
    val file = rootProject.file("local.properties")
    if (file.exists()) file.inputStream().use { load(it) }
}
''')
    default_extra = []
    if "maps" in r.flags:
        default_extra.append('        manifestPlaceholders["MAPS_API_KEY"] = localProperties.getProperty("MAPS_API_KEY", "")')
    for api in p.apis:
        if api.auth == "api_key":
            key = "API_KEY_" + to_snake(api.name).upper()
            default_extra.append(
                f'        buildConfigField("String", "{key}", "\\"${{localProperties.getProperty("{key}", "")}}\\"")')

    deps = []
    boms_by_conf = {}
    for key in r.libs:
        lib = LIBRARIES[key]
        if lib.bom:
            boms_by_conf.setdefault(lib.conf, set()).add(lib.bom)
    for conf in CONF_ORDER:
        group = [k for k in r.libs if LIBRARIES[k].conf == conf and not LIBRARIES[k].is_bom]
        if conf == "impl":
            group = [k for k in r.libs if LIBRARIES[k].conf == "impl" and not LIBRARIES[k].is_bom]
        if not group:
            continue
        for bom in sorted(boms_by_conf.get(conf, [])):
            deps.append(f"    {CONF_NAME[conf]}(platform({accessor(LIBRARIES[bom].alias)}))")
        for key in group:
            deps.append(f"    {CONF_NAME[conf]}({accessor(LIBRARIES[key].alias)})")
        deps.append("")

    app = f'''// Configuracao do modulo do aplicativo.
plugins {{
{plugins}
}}

{"".join(props_lines)}android {{
    namespace = "{p.package}"
    compileSdk = {p.compile_sdk}

    defaultConfig {{
        applicationId = "{p.package}"
        minSdk = {p.min_sdk}
        targetSdk = {p.target_sdk}
        versionCode = {p.version_code}
        versionName = "{p.version_name}"
        testInstrumentationRunner = "androidx.test.runner.AndroidJUnitRunner"
        vectorDrawables {{
            useSupportLibrary = true
        }}
{chr(10).join(default_extra)}
    }}

    buildTypes {{
        release {{
            isMinifyEnabled = false
            proguardFiles(
                getDefaultProguardFile("proguard-android-optimize.txt"),
                "proguard-rules.pro"
            )
        }}
    }}

    compileOptions {{
        sourceCompatibility = JavaVersion.VERSION_17
        targetCompatibility = JavaVersion.VERSION_17
    }}

    buildFeatures {{
{chr(10).join(build_features)}
    }}

    packaging {{
        resources {{
            excludes += "/META-INF/{{AL2.0,LGPL2.1}}"
        }}
    }}
}}

kotlin {{
    compilerOptions {{
        jvmTarget.set(org.jetbrains.kotlin.gradle.dsl.JvmTarget.JVM_17)
    }}
}}

dependencies {{
{chr(10).join(deps).rstrip()}
}}'''
    app = app.replace("\n\n\n", "\n\n")
    ctx.add("app/build.gradle.kts", app)

    # ----- gradle.properties e wrapper -----
    ctx.add("gradle.properties", '''# Configuracoes globais do Gradle.
org.gradle.jvmargs=-Xmx2048m -Dfile.encoding=UTF-8
org.gradle.parallel=true
org.gradle.caching=true
android.useAndroidX=true
android.nonTransitiveRClass=true
kotlin.code.style=official''')
    ctx.add("gradle/wrapper/gradle-wrapper.properties", f'''distributionBase=GRADLE_USER_HOME
distributionPath=wrapper/dists
distributionUrl=https\\://services.gradle.org/distributions/gradle-{v["gradle"]}-bin.zip
networkTimeout=10000
validateDistributionUrl=true
zipStoreBase=GRADLE_USER_HOME
zipStorePath=wrapper/dists''')

    proguard = ["# Regras do R8/ProGuard. Ative isMinifyEnabled no release para usar.",
                "-keepattributes Signature, *Annotation*, InnerClasses, EnclosingMethod"]
    if p.apis:
        proguard += ["", "# Modelos de API usados pelo Gson.", f"-keep class {p.package}.data.remote.** {{ *; }}"]
    if p.entities:
        proguard += ["", "# Entidades do Room.", f"-keep class {p.package}.data.local.** {{ *; }}"]
    ctx.add("app/proguard-rules.pro", "\n".join(proguard))

    ctx.add(".gitignore", '''# Arquivos gerados e locais que nao devem ir para o controle de versao.
*.iml
.gradle/
/local.properties
/.idea/
.DS_Store
/build
/captures
.externalNativeBuild
.cxx
app/build/
app/release/''')
    ctx.add("app/.gitignore", "/build")

    local = ["# Copie este arquivo para local.properties e preencha os valores.",
             "# O Android Studio adiciona sdk.dir automaticamente.", "# sdk.dir=/caminho/para/Android/Sdk"]
    if "maps" in r.flags:
        local.append("MAPS_API_KEY=coloque_sua_chave_do_google_maps")
    for api in p.apis:
        if api.auth == "api_key":
            local.append(f"API_KEY_{to_snake(api.name).upper()}=coloque_sua_chave")
    ctx.add("local.properties.example", "\n".join(local))
