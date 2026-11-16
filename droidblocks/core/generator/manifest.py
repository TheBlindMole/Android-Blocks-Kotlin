"""Geracao do AndroidManifest.xml."""

from ...catalog.features import PERMISSIONS
from ..naming import to_package_segment


def generate(ctx):
    p = ctx.project
    r = ctx.resolved
    lines = ['<?xml version="1.0" encoding="utf-8"?>',
             '<!-- Manifesto gerado pelo DroidBlocks. Permissoes e componentes vem das funcionalidades ativas. -->',
             '<manifest xmlns:android="http://schemas.android.com/apk/res/android"',
             '    xmlns:tools="http://schemas.android.com/tools">', '']
    for perm in r.permissions:
        meta = PERMISSIONS.get(perm, (False, None, None))
        if meta[2]:
            lines.append(f'    <uses-permission android:name="{perm}" android:maxSdkVersion="{meta[2]}" />')
        else:
            lines.append(f'    <uses-permission android:name="{perm}" />')
    extra_root = [f.manifest_root for f in r.features if f.manifest_root]
    if extra_root:
        lines.append("")
        lines.extend(dict.fromkeys(extra_root))
    queries = []
    for f in r.features:
        queries.extend(f.queries)
    if queries:
        lines += ["", "    <queries>"] + list(dict.fromkeys(queries)) + ["    </queries>"]

    splash = "splash" in r.flags
    app_attrs = [
        '        android:name=".App"',
        '        android:allowBackup="true"',
        '        android:dataExtractionRules="@xml/data_extraction_rules"',
        '        android:fullBackupContent="@xml/backup_rules"',
        '        android:icon="@mipmap/ic_launcher"',
        '        android:label="@string/app_name"',
        '        android:roundIcon="@mipmap/ic_launcher_round"',
        '        android:supportsRtl="true"',
        '        android:theme="@style/Theme.App"',
    ]
    if "locale_config" in r.flags:
        app_attrs.append('        android:localeConfig="@xml/locales_config"')
    app_attrs[-1] += '\n        tools:targetApi="31">'
    lines += ["", "    <application"] + app_attrs

    scheme = to_package_segment(p.name)
    deep_link = ""
    if "deep_links" in r.flags:
        deep_link = f'''
            <intent-filter>
                <action android:name="android.intent.action.VIEW" />
                <category android:name="android.intent.category.DEFAULT" />
                <category android:name="android.intent.category.BROWSABLE" />
                <data android:scheme="{scheme}" />
            </intent-filter>'''
    launcher = '''
            <intent-filter>
                <action android:name="android.intent.action.MAIN" />
                <category android:name="android.intent.category.LAUNCHER" />
            </intent-filter>'''
    theme_attr = '\n            android:theme="@style/Theme.App.Starting"' if splash else ""

    if ctx.compose:
        lines.append(f'''
        <activity
            android:name=".MainActivity"
            android:exported="true"
            android:windowSoftInputMode="adjustResize"{theme_attr}>{launcher}{deep_link}
        </activity>''')
    else:
        start = p.get_start_screen()
        for screen in p.screens:
            cls = ctx.screen_class(screen)
            pkg = ctx.screen_package(screen).replace(p.package, "")
            if screen is start:
                lines.append(f'''
        <activity
            android:name="{pkg}.{cls}Activity"
            android:exported="true"
            android:windowSoftInputMode="adjustResize"{theme_attr}>{launcher}{deep_link}
        </activity>''')
            else:
                lines.append(f'''
        <activity
            android:name="{pkg}.{cls}Activity"
            android:exported="false"
            android:windowSoftInputMode="adjustResize" />''')

    if "maps" in r.flags:
        lines.append('''
        <!-- Chave do Google Maps lida de local.properties (MAPS_API_KEY). -->
        <meta-data
            android:name="com.google.android.geo.API_KEY"
            android:value="${MAPS_API_KEY}" />''')
    extra_app = [f.manifest_app for f in r.features if f.manifest_app]
    for block in dict.fromkeys(extra_app):
        lines.append("")
        lines.append(block)
    lines += ["    </application>", "", "</manifest>"]
    ctx.add("app/src/main/AndroidManifest.xml", "\n".join(lines))
