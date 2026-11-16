"""Catalogo completo de funcionalidades disponiveis para os projetos."""

from .base import Feature, PERMISSIONS
from . import system, network, data, media, location, background, business, extras

ALL_FEATURES = (system.FEATURES + network.FEATURES + data.FEATURES + media.FEATURES
                + location.FEATURES + background.FEATURES + business.FEATURES + extras.FEATURES)

FEATURES = {f.key: f for f in ALL_FEATURES}

CATEGORY_ORDER = [
    "Sistema e dispositivo", "Rede e APIs", "Firebase (nuvem)", "Dados e armazenamento",
    "Midia e camera", "Inteligencia artificial (ML Kit)", "Localizacao e mapas",
    "Sensores e hardware", "Notificacoes e segundo plano", "Seguranca e autenticacao",
    "Comercio e pagamentos", "Social e comunicacao", "Produtividade e interface",
]


def by_category():
    """Agrupa as funcionalidades por categoria, na ordem de exibicao."""
    groups = {cat: [] for cat in CATEGORY_ORDER}
    for feature in ALL_FEATURES:
        groups.setdefault(feature.category, []).append(feature)
    return {k: v for k, v in groups.items() if v}


def get(key):
    return FEATURES.get(key)


__all__ = ["Feature", "PERMISSIONS", "FEATURES", "ALL_FEATURES", "by_category", "get"]
