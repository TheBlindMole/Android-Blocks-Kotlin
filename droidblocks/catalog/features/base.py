"""Estrutura base de uma funcionalidade (feature) do catalogo.

Cada funcionalidade descreve o que precisa ser adicionado ao projeto Android:
bibliotecas, permissoes, arquivos Kotlin, recursos, trechos de inicializacao
e dependencias de outras funcionalidades. O resolvedor junta tudo isso
automaticamente quando a funcionalidade e ativada.
"""

from dataclasses import dataclass, field


@dataclass
class Feature:
    key: str
    name: str
    category: str
    description: str
    libs: list = field(default_factory=list)
    libs_compose: list = field(default_factory=list)
    libs_views: list = field(default_factory=list)
    permissions: list = field(default_factory=list)
    files: dict = field(default_factory=dict)
    files_compose: dict = field(default_factory=dict)
    files_views: dict = field(default_factory=dict)
    requires: list = field(default_factory=list)
    app_init: list = field(default_factory=list)
    activity_init: list = field(default_factory=list)
    manifest_app: str = ""
    manifest_root: str = ""
    queries: list = field(default_factory=list)
    res: dict = field(default_factory=dict)
    assets: dict = field(default_factory=dict)
    plugins: list = field(default_factory=list)
    flags: list = field(default_factory=list)
    notes: str = ""
    builtin: bool = False


# Metadados de permissoes: (perigosa/runtime, api minima para pedir, maxSdkVersion)
PERMISSIONS = {
    "android.permission.INTERNET": (False, None, None),
    "android.permission.ACCESS_NETWORK_STATE": (False, None, None),
    "android.permission.ACCESS_WIFI_STATE": (False, None, None),
    "android.permission.VIBRATE": (False, None, None),
    "android.permission.CAMERA": (True, None, None),
    "android.permission.RECORD_AUDIO": (True, None, None),
    "android.permission.ACCESS_FINE_LOCATION": (True, None, None),
    "android.permission.ACCESS_COARSE_LOCATION": (True, None, None),
    "android.permission.ACCESS_BACKGROUND_LOCATION": (False, None, None),
    "android.permission.POST_NOTIFICATIONS": (True, 33, None),
    "android.permission.READ_CONTACTS": (True, None, None),
    "android.permission.ACTIVITY_RECOGNITION": (True, 29, None),
    "android.permission.BLUETOOTH_SCAN": (True, 31, None),
    "android.permission.BLUETOOTH_CONNECT": (True, 31, None),
    "android.permission.BLUETOOTH": (False, None, 30),
    "android.permission.BLUETOOTH_ADMIN": (False, None, 30),
    "android.permission.NFC": (False, None, None),
    "android.permission.RECEIVE_BOOT_COMPLETED": (False, None, None),
    "android.permission.FOREGROUND_SERVICE": (False, None, None),
    "android.permission.FOREGROUND_SERVICE_DATA_SYNC": (False, None, None),
    "android.permission.WRITE_EXTERNAL_STORAGE": (False, None, 28),
    "android.permission.USE_BIOMETRIC": (False, None, None),
    "android.permission.WAKE_LOCK": (False, None, None),
    "com.google.android.gms.permission.AD_ID": (False, None, None),
}
