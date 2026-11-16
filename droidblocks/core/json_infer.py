"""Inferencia de modelos de API a partir de um JSON de exemplo (funciona offline)."""

import json

from .model import ApiModel, ApiField
from .naming import to_pascal


def _type_of(value, key, models, used):
    if isinstance(value, bool):
        return "Boolean"
    if isinstance(value, int):
        return "Long" if abs(value) > 2_000_000_000 or key.lower() in ("id", "timestamp") else "Int"
    if isinstance(value, float):
        return "Double"
    if isinstance(value, str) or value is None:
        return "String"
    if isinstance(value, list):
        first = next((v for v in value if v is not None), None)
        if isinstance(first, dict):
            name = _model(first, to_pascal(key.rstrip("s") or key, "Item"), models, used)
            return f"List<{name}>"
        if isinstance(first, bool):
            return "List<Boolean>"
        if isinstance(first, (int, float)):
            return "List<Double>"
        return "List<String>"
    if isinstance(value, dict):
        numeric = value and all(isinstance(v, (int, float)) and not isinstance(v, bool) for v in value.values())
        if numeric and len(value) > 8:
            return "Map<String,Double>"
        return _model(value, to_pascal(key, "Item"), models, used)
    return "String"


def _model(obj, name, models, used):
    base = name
    index = 2
    while name in used:
        name = f"{base}{index}"
        index += 1
    used.add(name)
    model = ApiModel(name, [])
    models.append(model)
    for key, value in obj.items():
        model.fields.append(ApiField(key, _type_of(value, key, models, used)))
    return name


def infer(json_text, root_name="Response"):
    """Retorna (modelos, nome_do_modelo_de_resposta, retorna_lista, campo_wrapper)."""
    data = json.loads(json_text)
    models, used = [], set()
    if isinstance(data, list):
        first = next((v for v in data if isinstance(v, dict)), None)
        if first is None:
            raise ValueError("A lista do JSON nao contem objetos.")
        name = _model(first, to_pascal(root_name, "Item"), models, used)
        return models, name, True, ""
    if not isinstance(data, dict):
        raise ValueError("O JSON precisa ser um objeto ou uma lista de objetos.")
    name = _model(data, to_pascal(root_name, "Response"), models, used)
    wrapper = ""
    for key, value in data.items():
        if isinstance(value, list) and value and isinstance(value[0], dict):
            wrapper = key
            break
    return models, name, False, wrapper
