"""Modelo de dados de um projeto do DroidBlocks.

Tudo e serializavel em JSON (arquivos .dbp) por meio de to_dict/from_dict.
"""

import copy
import uuid
from dataclasses import dataclass, field, asdict

from .naming import to_pascal, to_package_segment

PROJECT_FORMAT_VERSION = 1


def new_id(prefix="c"):
    """Gera um identificador curto e unico para blocos e telas."""
    return prefix + uuid.uuid4().hex[:8]


@dataclass
class Component:
    """Um bloco visual posicionado dentro de uma tela."""
    type: str
    props: dict = field(default_factory=dict)
    id: str = field(default_factory=new_id)


@dataclass
class Screen:
    """Uma tela do aplicativo, composta por uma pilha de blocos."""
    name: str
    title: str = ""
    components: list = field(default_factory=list)
    in_nav: bool = False
    icon: str = "home"
    form_entity: str = ""
    id: str = field(default_factory=lambda: new_id("s"))

    @property
    def class_name(self):
        return to_pascal(self.name, "Screen")


@dataclass
class ApiField:
    """Campo de um modelo de resposta de API."""
    name: str
    type: str = "String"


@dataclass
class ApiModel:
    """Modelo (DTO) usado em requisicoes e respostas."""
    name: str
    fields: list = field(default_factory=list)


@dataclass
class Endpoint:
    """Endpoint REST de uma API."""
    name: str
    method: str = "GET"
    path: str = ""
    model: str = ""
    returns_list: bool = True
    wrapper_field: str = ""
    query: str = ""
    body_model: str = ""
    mapping: dict = field(default_factory=dict)


@dataclass
class Api:
    """Configuracao de uma API REST consumida pelo app."""
    name: str
    base_url: str = "https://"
    auth: str = "none"
    api_key_header: str = "X-API-Key"
    endpoints: list = field(default_factory=list)
    models: list = field(default_factory=list)


@dataclass
class Entity:
    """Entidade persistida no banco de dados local (Room)."""
    name: str
    fields: list = field(default_factory=list)


@dataclass
class Project:
    """Projeto completo de aplicativo Android."""
    name: str = "MeuApp"
    package: str = "com.exemplo.meuapp"
    description: str = ""
    ui_mode: str = "compose"
    min_sdk: int = 24
    target_sdk: int = 35
    compile_sdk: int = 35
    navigation: str = "stack"
    theme_mode: str = "system"
    primary_color: str = "#1E88E5"
    secondary_color: str = "#0D47A1"
    tertiary_color: str = "#26C6DA"
    languages: list = field(default_factory=lambda: ["pt", "en"])
    request_permissions_on_start: bool = True
    version_name: str = "1.0.0"
    version_code: int = 1
    screens: list = field(default_factory=list)
    start_screen: str = ""
    features: list = field(default_factory=list)
    algorithms: list = field(default_factory=list)
    apis: list = field(default_factory=list)
    entities: list = field(default_factory=list)
    database_name: str = "app_database"
    samples: dict = field(default_factory=dict)
    versions: dict = field(default_factory=dict)
    template: str = ""
    format_version: int = PROJECT_FORMAT_VERSION

    # ----- consultas utilitarias -----

    def screen_by_name(self, name):
        for screen in self.screens:
            if screen.name == name:
                return screen
        return None

    def screen_by_id(self, sid):
        for screen in self.screens:
            if screen.id == sid:
                return screen
        return None

    def entity_by_name(self, name):
        for entity in self.entities:
            if entity.name == name:
                return entity
        return None

    def api_by_name(self, name):
        for api in self.apis:
            if api.name == name:
                return api
        return None

    def get_start_screen(self):
        screen = self.screen_by_name(self.start_screen)
        if screen is None and self.screens:
            screen = self.screens[0]
        return screen

    def clone(self):
        return copy.deepcopy(self)

    @property
    def class_prefix(self):
        return to_pascal(self.name, "App")

    # ----- serializacao -----

    def to_dict(self):
        return asdict(self)

    @staticmethod
    def from_dict(data):
        data = dict(data or {})
        project = Project()
        simple = {k: v for k, v in data.items() if k not in
                  {"screens", "apis", "entities"} and hasattr(project, k)}
        for key, value in simple.items():
            setattr(project, key, value)
        project.screens = []
        for s in data.get("screens", []):
            comps = [Component(type=c.get("type", "text"), props=dict(c.get("props", {})),
                               id=c.get("id") or new_id()) for c in s.get("components", [])]
            project.screens.append(Screen(
                name=s.get("name", "Tela"), title=s.get("title", ""), components=comps,
                in_nav=bool(s.get("in_nav", False)), icon=s.get("icon", "home"),
                form_entity=s.get("form_entity", ""), id=s.get("id") or new_id("s")))
        project.apis = []
        for a in data.get("apis", []):
            models = [ApiModel(name=m.get("name", "Model"),
                               fields=[ApiField(**f) for f in m.get("fields", [])])
                      for m in a.get("models", [])]
            endpoints = [Endpoint(**{k: v for k, v in e.items() if k in Endpoint.__dataclass_fields__})
                         for e in a.get("endpoints", [])]
            project.apis.append(Api(name=a.get("name", "Api"), base_url=a.get("base_url", ""),
                                    auth=a.get("auth", "none"),
                                    api_key_header=a.get("api_key_header", "X-API-Key"),
                                    endpoints=endpoints, models=models))
        project.entities = [Entity(name=e.get("name", "Item"),
                                   fields=[list(f) for f in e.get("fields", [])])
                            for e in data.get("entities", [])]
        return project


def default_package(name, company="exemplo"):
    """Sugere um applicationId a partir do nome do projeto."""
    return f"com.{to_package_segment(company)}.{to_package_segment(name)}"


def parse_fields(text):
    """Converte linhas 'nome:Tipo' em lista [nome, Tipo]."""
    result = []
    for raw in (text or "").replace(",", "\n").split("\n"):
        raw = raw.strip()
        if not raw:
            continue
        if ":" in raw:
            name, ftype = raw.split(":", 1)
        else:
            name, ftype = raw, "String"
        result.append([name.strip(), ftype.strip() or "String"])
    return result


def fields_to_text(fields):
    """Converte lista de campos em texto editavel 'nome:Tipo' por linha."""
    lines = []
    for f in fields:
        if isinstance(f, ApiField):
            lines.append(f"{f.name}:{f.type}")
        else:
            lines.append(f"{f[0]}:{f[1]}")
    return "\n".join(lines)
