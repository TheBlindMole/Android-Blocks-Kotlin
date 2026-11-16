"""Resolvedor de dependencias e diagnostico do projeto.

A partir das telas, blocos, acoes, APIs e entidades, descobre automaticamente
quais funcionalidades, bibliotecas, plugins e permissoes sao necessarias,
e aponta problemas antes da geracao do codigo.
"""

from dataclasses import dataclass, field

from ..catalog import features as feature_catalog
from ..catalog.features import PERMISSIONS
from ..catalog.components import (COMPONENTS, ACTIONS, parse_action, INPUT_COMPONENTS, LIST_COMPONENTS,
                                   split_actions, join_actions)
from ..catalog.algorithms import ALGORITHMS, ALGO_REQUIRES
from ..catalog.libraries import (LIBRARIES, BASE_LIBS_COMMON, BASE_LIBS_COMPOSE,
                                 BASE_LIBS_VIEWS)
from .naming import to_pascal, to_snake, to_camel, is_valid_package
from .model import Screen, Component, new_id

SOURCE_FEATURES = {"cart": "cart", "favorites": "favorites", "chat": "chat", "contacts": "contacts"}


@dataclass
class Resolved:
    features: list = field(default_factory=list)
    feature_keys: set = field(default_factory=set)
    auto_added: list = field(default_factory=list)
    libs: list = field(default_factory=list)
    plugins: list = field(default_factory=list)
    permissions: list = field(default_factory=list)
    algorithms: list = field(default_factory=list)
    flags: set = field(default_factory=set)
    diagnostics: list = field(default_factory=list)

    def has(self, key):
        return key in self.feature_keys

    def _add(self, level, message):
        # Evita repetir a mesma mensagem quando varios blocos tem o mesmo problema.
        if (level, message) not in self.diagnostics:
            self.diagnostics.append((level, message))

    def warn(self, message):
        self._add("aviso", message)

    def error(self, message):
        self._add("erro", message)

    def info(self, message):
        self._add("info", message)

    @property
    def errors(self):
        return [m for level, m in self.diagnostics if level == "erro"]


def iter_actions(project):
    """Percorre todas as acoes configuradas: (tela, bloco, propriedade, chave, argumento)."""
    for screen in project.screens:
        for comp in screen.components:
            spec = COMPONENTS.get(comp.type)
            if not spec:
                continue
            for prop in spec.props:
                if prop.kind == "action":
                    for part in split_actions(comp.props.get(prop.key, "")):
                        key, arg = parse_action(part)
                        yield screen, comp, prop.key, key, arg


def iter_sources(project):
    for screen in project.screens:
        for comp in screen.components:
            if comp.type in LIST_COMPONENTS:
                yield screen, comp, comp.props.get("source", "sample:default")


def required_features(project):
    """Funcionalidades exigidas implicitamente pelo conteudo do projeto."""
    needed = []
    for screen in project.screens:
        for comp in screen.components:
            spec = COMPONENTS.get(comp.type)
            if spec:
                needed.extend(spec.requires)
            if comp.type == "text_field" and comp.props.get("validation", "none") != "none":
                needed.append("validators")
    for _, _, _, key, _ in iter_actions(project):
        feature = ACTIONS[key].feature
        if feature:
            needed.append(feature)
    for _, _, source in iter_sources(project):
        if source in SOURCE_FEATURES:
            needed.append(SOURCE_FEATURES[source])
        elif source.startswith("api:"):
            needed.append("network")
    if project.entities:
        needed.append("room")
    if project.apis:
        needed.append("network")
        if any(api.auth == "bearer" for api in project.apis):
            needed.append("auth_token")
    return needed


def resolve(project):
    """Calcula tudo que o projeto precisa e devolve um Resolved com diagnosticos."""
    result = Resolved()
    catalog = feature_catalog.FEATURES
    requested = [k for k in project.features if k in catalog]
    for key in project.features:
        if key not in catalog:
            result.warn(f"Funcionalidade desconhecida ignorada: {key}")
    implicit = required_features(project)

    ordered = []
    pending = list(requested) + implicit
    while pending:
        key = pending.pop(0)
        if key in ordered or key not in catalog:
            continue
        ordered.append(key)
        pending.extend(catalog[key].requires)
    result.feature_keys = set(ordered)
    result.features = [catalog[k] for k in ordered]
    result.auto_added = [k for k in ordered if k not in requested]

    # Bibliotecas
    compose = project.ui_mode == "compose"
    libs = list(BASE_LIBS_COMMON) + (BASE_LIBS_COMPOSE if compose else BASE_LIBS_VIEWS)
    for feature in result.features:
        libs.extend(feature.libs)
        libs.extend(feature.libs_compose if compose else feature.libs_views)
        result.flags.update(feature.flags)
    for lib in list(libs):
        bom = LIBRARIES[lib].bom
        if bom:
            libs.append(bom)
    result.libs = list(dict.fromkeys(l for l in libs if l in LIBRARIES))

    # Plugins
    plugins = ["android_application", "kotlin_android"]
    if compose:
        plugins.append("kotlin_compose")
    for feature in result.features:
        plugins.extend(feature.plugins)
    result.plugins = list(dict.fromkeys(plugins))

    # Permissoes
    perms = ["android.permission.INTERNET"]
    for feature in result.features:
        perms.extend(feature.permissions)
    result.permissions = list(dict.fromkeys(perms))

    # Algoritmos
    algos = []
    pending = [a for a in project.algorithms if a in ALGORITHMS]
    while pending:
        key = pending.pop(0)
        if key not in algos:
            algos.append(key)
            pending.extend(ALGO_REQUIRES.get(key, []))
    result.algorithms = algos

    _diagnose(project, result)
    return result


def _diagnose(project, result):
    if not project.name.strip():
        result.error("O projeto precisa de um nome.")
    if not is_valid_package(project.package):
        result.error(f"Pacote invalido: '{project.package}'. Use o formato com.empresa.app (minusculas).")
    if project.min_sdk > project.target_sdk:
        result.error("O SDK minimo nao pode ser maior que o SDK alvo.")
    if not project.screens:
        result.error("Adicione pelo menos uma tela.")
        return
    if project.start_screen and not project.screen_by_name(project.start_screen):
        result.warn(f"Tela inicial '{project.start_screen}' nao existe; a primeira tela sera usada.")

    names = {}
    for screen in project.screens:
        cls = to_pascal(screen.name, "Screen")
        if cls in names:
            result.error(f"As telas '{screen.name}' e '{names[cls]}' geram o mesmo nome de classe ({cls}).")
        names[cls] = screen.name
        keys = {}
        fabs = 0
        for comp in screen.components:
            if comp.type not in COMPONENTS:
                result.warn(f"Tela {screen.name}: bloco desconhecido '{comp.type}' sera ignorado.")
                continue
            if comp.type == "fab":
                fabs += 1
            if comp.type in INPUT_COMPONENTS:
                key = to_camel(comp.props.get("key", ""), "field")
                if key in keys and keys[key] != comp.type:
                    result.warn(f"Tela {screen.name}: a chave '{key}' e usada por blocos de tipos diferentes.")
                keys[key] = comp.type
        if fabs > 1:
            result.warn(f"Tela {screen.name}: apenas um botao flutuante sera exibido.")
        if screen.form_entity and not project.entity_by_name(screen.form_entity):
            result.warn(f"Tela {screen.name}: entidade do formulario '{screen.form_entity}' nao existe.")

    for screen, comp, prop, key, arg in iter_actions(project):
        action = ACTIONS[key]
        if action.arg == "screen" and arg and not project.screen_by_name(arg):
            result.warn(f"Tela {screen.name}: a acao '{action.label}' aponta para a tela inexistente '{arg}'.")
        if action.arg == "endpoint" and not _endpoint_exists(project, arg):
            result.warn(f"Tela {screen.name}: endpoint de API '{arg}' nao encontrado.")
        if key in ("login", "register"):
            fields = _input_keys(screen)
            if "email" not in fields or "password" not in fields:
                result.warn(f"Tela {screen.name}: login/cadastro precisa de campos com chave 'email' e 'password'.")
        if key == "send_message" and "message" not in _input_keys(screen):
            result.warn(f"Tela {screen.name}: 'Enviar mensagem' precisa de um campo com chave 'message'.")

    for screen, comp, source in iter_sources(project):
        if source.startswith("entity:") and not project.entity_by_name(source[7:]):
            result.warn(f"Tela {screen.name}: a lista usa a entidade inexistente '{source[7:]}'.")
        elif source.startswith("api:") and not _endpoint_exists(project, source[4:]):
            result.warn(f"Tela {screen.name}: a lista usa o endpoint inexistente '{source[4:]}'.")
        elif source.startswith("sample:") and source[7:] not in project.samples and source[7:] != "default":
            result.info(f"Tela {screen.name}: conjunto de exemplo '{source[7:]}' nao existe; serao usados itens genericos.")

    reachable = reachable_screens(project)
    for screen in project.screens:
        if screen.name not in reachable:
            result.warn(f"A tela '{screen.name}' fica inacessivel: nenhuma acao ou menu leva ate ela.")
        if not [c for c in screen.components if c.type in COMPONENTS]:
            result.info(f"A tela '{screen.name}' esta vazia.")
    for screen, comp, prop, key, arg in iter_actions(project):
        if prop == "item_action" and key == "navigate" and arg:
            target = project.screen_by_name(arg)
            if target and not any(c.type == "item_detail" for c in target.components):
                result.info(f"A lista em {screen.name} abre '{arg}', que nao tem o bloco 'Detalhe do item'.")

    nav_screens = [s for s in project.screens if s.in_nav]
    if project.navigation in ("bottom", "drawer") and not nav_screens:
        result.warn("Navegacao inferior/lateral escolhida, mas nenhuma tela esta marcada como 'no menu'.")
    if project.navigation == "bottom" and len(nav_screens) > 5:
        result.warn("A barra inferior comporta ate 5 telas; as demais nao aparecerao nela.")

    for entity in project.entities:
        if not entity.fields:
            result.warn(f"A entidade {entity.name} nao tem campos.")
    for api in project.apis:
        if not api.base_url.startswith("http"):
            result.error(f"A API {api.name} precisa de uma URL base valida (http/https).")

    for feature in result.features:
        if feature.notes:
            result.info(f"{feature.name}: {feature.notes}")
    if result.auto_added:
        names = ", ".join(feature_catalog.FEATURES[k].name for k in result.auto_added)
        result.info(f"Adicionadas automaticamente: {names}")
    dangerous = [p for p in result.permissions if PERMISSIONS.get(p, (False,))[0]]
    if dangerous:
        short = ", ".join(p.split(".")[-1] for p in dangerous)
        result.info(f"Permissoes solicitadas ao usuario em tempo de execucao: {short}")


SCREEN_ACTIONS = {"navigate", "submit", "login", "register", "logout", "checkout", "biometric", "finish_onboarding"}


def navigation_edges(project):
    """Arestas (origem, destino, acao) do fluxo de navegacao entre telas."""
    edges = []
    for screen, comp, prop, key, arg in iter_actions(project):
        if key in SCREEN_ACTIONS and arg and project.screen_by_name(arg):
            edges.append((screen.name, arg, key))
    return edges


def reachable_screens(project):
    """Telas alcancaveis a partir da tela inicial, das telas do menu e das acoes."""
    start = project.get_start_screen()
    if start is None:
        return set()
    seen = {start.name}
    if project.navigation in ("bottom", "drawer"):
        seen |= {s.name for s in project.screens if s.in_nav}
    edges = navigation_edges(project)
    changed = True
    while changed:
        changed = False
        for origin, target, _ in edges:
            if origin in seen and target not in seen:
                seen.add(target)
                changed = True
    return seen


def _input_keys(screen):
    return {to_camel(c.props.get("key", ""), "field") for c in screen.components if c.type in INPUT_COMPONENTS}


def _endpoint_exists(project, ref):
    if "." not in (ref or ""):
        return False
    api_name, endpoint = ref.split(".", 1)
    api = project.api_by_name(api_name)
    return bool(api and any(e.name == endpoint for e in api.endpoints))


def auto_organize(project):
    """Corrige e organiza o projeto automaticamente. Retorna a lista de mudancas feitas."""
    changes = []
    # Nomes de tela unicos
    used = set()
    for screen in project.screens:
        base = to_pascal(screen.name, "Tela")
        name = base
        index = 2
        while name in used:
            name = f"{base}{index}"
            index += 1
        if name != screen.name:
            changes.append(f"Tela '{screen.name}' renomeada para '{name}'.")
            screen.name = name
        used.add(name)
        if not screen.title:
            screen.title = name
    # Telas inexistentes referenciadas por acoes
    for screen in list(project.screens):
        for comp in screen.components:
            spec = COMPONENTS.get(comp.type)
            if not spec:
                continue
            for prop in spec.props:
                if prop.kind != "action":
                    continue
                parts = []
                for part in split_actions(comp.props.get(prop.key, "")):
                    key, arg = parse_action(part)
                    if ACTIONS[key].arg == "screen" and arg:
                        target = to_pascal(arg, "Tela")
                        if not project.screen_by_name(target):
                            project.screens.append(Screen(name=target, title=arg, components=[
                                Component(type="title", props={"text": arg, "size": "large", "align": "start"}, id=new_id())]))
                            changes.append(f"Tela '{target}' criada (referenciada por uma acao em {screen.name}).")
                        part = f"{key}:{target}"
                    parts.append(part)
                comp.props[prop.key] = join_actions(parts)
    # Tela inicial
    if not project.screen_by_name(project.start_screen) and project.screens:
        project.start_screen = project.screens[0].name
        changes.append(f"Tela inicial definida como '{project.start_screen}'.")
    # Fontes de lista quebradas
    for screen, comp, source in list(iter_sources(project)):
        broken = (source.startswith("entity:") and not project.entity_by_name(source[7:])) or \
                 (source.startswith("api:") and not _endpoint_exists(project, source[4:]))
        if broken:
            comp.props["source"] = "sample:default"
            changes.append(f"Lista em {screen.name} com fonte invalida trocada por dados de exemplo.")
    # Menu de navegacao
    if project.navigation in ("bottom", "drawer") and not any(s.in_nav for s in project.screens):
        for screen in project.screens[:4]:
            if not screen.form_entity:
                screen.in_nav = True
        changes.append("Telas principais adicionadas ao menu de navegacao.")
    # Ordena: tela inicial primeiro, depois telas do menu
    start = project.get_start_screen()
    ordered = sorted(project.screens, key=lambda s: (s is not start, not s.in_nav))
    if [s.id for s in ordered] != [s.id for s in project.screens]:
        project.screens = ordered
        changes.append("Telas reordenadas (inicial e menu primeiro).")
    # Torna explicitas as funcionalidades exigidas
    resolved = resolve(project)
    for key in resolved.auto_added:
        if key not in project.features:
            project.features.append(key)
    if resolved.auto_added:
        changes.append(f"{len(resolved.auto_added)} funcionalidades de suporte adicionadas a lista do projeto.")
    # Remove blocos desconhecidos
    for screen in project.screens:
        before = len(screen.components)
        screen.components = [c for c in screen.components if c.type in COMPONENTS]
        if len(screen.components) != before:
            changes.append(f"Blocos invalidos removidos de {screen.name}.")
    if not changes:
        changes.append("Nada a corrigir: o projeto ja esta organizado.")
    return changes


def route_of(screen):
    return to_snake(screen.name, "screen")
