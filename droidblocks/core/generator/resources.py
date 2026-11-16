"""Geracao de recursos Android: cores, temas, icones, menus e XMLs auxiliares."""

from ...catalog.components import ICONS
from ..png import render_icon, hex_to_rgb
from ..naming import xml_escape

MIPMAPS = {"mdpi": 48, "hdpi": 72, "xhdpi": 96, "xxhdpi": 144, "xxxhdpi": 192}


def mix(color, other, amount):
    """Mistura duas cores hexadecimais (amount 0..1 em direcao a 'other')."""
    a = hex_to_rgb(color)
    b = hex_to_rgb(other)
    return "#%02X%02X%02X" % tuple(int(a[i] + (b[i] - a[i]) * amount) for i in range(3))


def argb(color):
    return "#FF" + color.lstrip("#").upper()


def rounded_rect_path(x0, y0, x1, y1, r):
    return (f"M{x0 + r},{y0} H{x1 - r} Q{x1},{y0} {x1},{y0 + r} V{y1 - r} Q{x1},{y1} {x1 - r},{y1} "
            f"H{x0 + r} Q{x0},{y1} {x0},{y1 - r} V{y0 + r} Q{x0},{y0} {x0 + r},{y0} Z")


def vector(path, color="#FF000000", size=24, viewport=24, comment="Icone vetorial."):
    return f'''<?xml version="1.0" encoding="utf-8"?>
<!-- {comment} -->
<vector xmlns:android="http://schemas.android.com/apk/res/android"
    android:width="{size}dp"
    android:height="{size}dp"
    android:viewportWidth="{viewport}"
    android:viewportHeight="{viewport}">
    <path
        android:fillColor="{color}"
        android:pathData="{path}" />
</vector>'''


def generate(ctx):
    p = ctx.project
    r = ctx.resolved
    primary = p.primary_color
    secondary = p.secondary_color
    tertiary = p.tertiary_color

    ctx.add_res("values/colors.xml", f'''<?xml version="1.0" encoding="utf-8"?>
<!-- Paleta do aplicativo definida no DroidBlocks. -->
<resources>
    <color name="brand_primary">{argb(primary)}</color>
    <color name="brand_primary_dark">{argb(mix(primary, "#000000", 0.25))}</color>
    <color name="brand_secondary">{argb(secondary)}</color>
    <color name="brand_tertiary">{argb(tertiary)}</color>
    <color name="ic_launcher_background">{argb(primary)}</color>
    <color name="white">#FFFFFFFF</color>
    <color name="black">#FF000000</color>
</resources>''')

    splash = "splash" in r.flags
    splash_style = '''
    <!-- Tema da tela de abertura (SplashScreen API). -->
    <style name="Theme.App.Starting" parent="Theme.SplashScreen">
        <item name="windowSplashScreenBackground">@color/brand_primary</item>
        <item name="windowSplashScreenAnimatedIcon">@drawable/ic_launcher_foreground</item>
        <item name="postSplashScreenTheme">@style/Theme.App</item>
    </style>''' if splash else ""

    if ctx.compose:
        light_parent = "android:Theme.Material.Light.NoActionBar"
        dark_parent = "android:Theme.Material.NoActionBar"
        if p.theme_mode == "dark":
            light_parent = dark_parent
        ctx.add_res("values/themes.xml", f'''<?xml version="1.0" encoding="utf-8"?>
<!-- Tema base da janela. As cores da interface ficam em ui/theme/Theme.kt (Compose). -->
<resources>
    <style name="Theme.App" parent="{light_parent}">
        <item name="android:windowBackground">@color/white</item>
    </style>{splash_style}
</resources>''')
        if p.theme_mode != "light":
            ctx.add_res("values-night/themes.xml", f'''<?xml version="1.0" encoding="utf-8"?>
<!-- Tema base da janela no modo escuro. -->
<resources>
    <style name="Theme.App" parent="{dark_parent}">
        <item name="android:windowBackground">@color/black</item>
    </style>
</resources>''')
    else:
        parent = {"light": "Theme.Material3.Light.NoActionBar",
                  "dark": "Theme.Material3.Dark.NoActionBar"}.get(p.theme_mode, "Theme.Material3.DayNight.NoActionBar")
        if "theme_toggle" in r.flags:
            parent = "Theme.Material3.DayNight.NoActionBar"
        ctx.add_res("values/themes.xml", f'''<?xml version="1.0" encoding="utf-8"?>
<!-- Tema Material 3 do aplicativo com a paleta escolhida. -->
<resources>
    <style name="Theme.App" parent="{parent}">
        <item name="colorPrimary">@color/brand_primary</item>
        <item name="colorOnPrimary">@color/white</item>
        <item name="colorSecondary">@color/brand_secondary</item>
        <item name="colorTertiary">@color/brand_tertiary</item>
        <item name="colorPrimaryContainer">{argb(mix(primary, "#FFFFFF", 0.8))}</item>
        <item name="colorOnPrimaryContainer">@color/brand_primary_dark</item>
    </style>{splash_style}
</resources>''')
        if p.theme_mode != "light":
            ctx.add_res("values-night/themes.xml", f'''<?xml version="1.0" encoding="utf-8"?>
<!-- Ajustes de cor para o modo escuro. -->
<resources>
    <style name="Theme.App" parent="{parent}">
        <item name="colorPrimary">{argb(mix(primary, "#FFFFFF", 0.35))}</item>
        <item name="colorOnPrimary">@color/black</item>
        <item name="colorSecondary">{argb(mix(secondary, "#FFFFFF", 0.35))}</item>
        <item name="colorTertiary">{argb(mix(tertiary, "#FFFFFF", 0.35))}</item>
        <item name="colorPrimaryContainer">@color/brand_primary_dark</item>
        <item name="colorOnPrimaryContainer">@color/white</item>
    </style>
</resources>''')

    # ----- icones do launcher -----
    blocks = [(33, 61, 75, 73), (39, 47, 69, 59), (45, 34, 63, 45)]
    path = " ".join(rounded_rect_path(*b, 2) for b in blocks)
    ctx.add_res("drawable/ic_launcher_foreground.xml", vector(
        path, "#FFFFFFFF", 108, 108, "Primeiro plano do icone adaptativo (blocos empilhados)."))
    adaptive = '''<?xml version="1.0" encoding="utf-8"?>
<!-- Icone adaptativo (Android 8+). -->
<adaptive-icon xmlns:android="http://schemas.android.com/apk/res/android">
    <background android:drawable="@color/ic_launcher_background" />
    <foreground android:drawable="@drawable/ic_launcher_foreground" />
    <monochrome android:drawable="@drawable/ic_launcher_foreground" />
</adaptive-icon>'''
    ctx.add_res("mipmap-anydpi-v26/ic_launcher.xml", adaptive)
    ctx.add_res("mipmap-anydpi-v26/ic_launcher_round.xml", adaptive)
    for density, size in (() if getattr(ctx, "preview", False) else MIPMAPS.items()):
        ctx.add_res(f"mipmap-{density}/ic_launcher.png", render_icon(size, primary, False))
        ctx.add_res(f"mipmap-{density}/ic_launcher_round.png", render_icon(size, primary, True))

    # ----- backup -----
    ctx.add_res("xml/backup_rules.xml", '''<?xml version="1.0" encoding="utf-8"?>
<!-- Regras de backup automatico (Android 6 a 11). -->
<full-backup-content>
    <include domain="sharedpref" path="." />
    <include domain="database" path="." />
</full-backup-content>''')
    ctx.add_res("xml/data_extraction_rules.xml", '''<?xml version="1.0" encoding="utf-8"?>
<!-- Regras de backup na nuvem e transferencia entre aparelhos (Android 12+). -->
<data-extraction-rules>
    <cloud-backup>
        <include domain="sharedpref" path="." />
        <include domain="database" path="." />
    </cloud-backup>
    <device-transfer>
        <include domain="sharedpref" path="." />
        <include domain="database" path="." />
    </device-transfer>
</data-extraction-rules>''')
    if "locale_config" in r.flags:
        locales = "\n".join(f'    <locale android:name="{lang}" />' for lang in (p.languages or ["pt"]))
        ctx.add_res("xml/locales_config.xml", f'''<?xml version="1.0" encoding="utf-8"?>
<!-- Idiomas oferecidos nas configuracoes de idioma por app (Android 13+). -->
<locale-config xmlns:android="http://schemas.android.com/apk/res/android">
{locales}
</locale-config>''')

    # ----- recursos extras das funcionalidades -----
    for feature in r.features:
        for path, content in feature.res.items():
            ctx.add_res(path, content)
        for path, content in feature.assets.items():
            ctx.add(f"app/src/main/assets/{path}", content)

    if not ctx.compose:
        _views_resources(ctx)


def _views_resources(ctx):
    p = ctx.project
    ctx.add_res("drawable/ic_menu.xml", vector("M3,18h18v-2H3v2zM3,13h18v-2H3v2zM3,6v2h18V6H3z", "#FFFFFFFF",
                                               comment="Icone do menu lateral."))
    ctx.add_res("drawable/ic_arrow_back.xml", vector(
        "M20,11H7.83l5.59,-5.59L12,4l-8,8 8,8 1.41,-1.41L7.83,13H20v-2z", "#FFFFFFFF", comment="Icone de voltar."))
    ctx.add_res("drawable/ic_star.xml", vector(ICONS["star"][1], "#FFFFC107", comment="Estrela de avaliacao."))
    ctx.add_res("drawable/bg_avatar.xml", '''<?xml version="1.0" encoding="utf-8"?>
<!-- Fundo circular para avatares. -->
<shape xmlns:android="http://schemas.android.com/apk/res/android" android:shape="oval">
    <solid android:color="@color/brand_primary" />
</shape>''')
    ctx.add_res("drawable/bg_banner.xml", '''<?xml version="1.0" encoding="utf-8"?>
<!-- Fundo arredondado em degrade para banners. -->
<shape xmlns:android="http://schemas.android.com/apk/res/android" android:shape="rectangle">
    <corners android:radius="16dp" />
    <gradient
        android:angle="0"
        android:endColor="@color/brand_secondary"
        android:startColor="@color/brand_primary" />
</shape>''')
    ctx.add_res("drawable/bg_scrim.xml", '''<?xml version="1.0" encoding="utf-8"?>
<!-- Degrade escuro de baixo para cima, deixa o texto legivel sobre imagens. -->
<shape xmlns:android="http://schemas.android.com/apk/res/android" android:shape="rectangle">
    <gradient
        android:angle="90"
        android:endColor="#00000000"
        android:startColor="#CC000000" />
</shape>''')
    ctx.add_res("drawable/bg_step_on.xml", '''<?xml version="1.0" encoding="utf-8"?>
<!-- Etapa concluida ou atual. -->
<shape xmlns:android="http://schemas.android.com/apk/res/android" android:shape="oval">
    <solid android:color="@color/brand_primary" />
</shape>''')
    ctx.add_res("drawable/bg_step_off.xml", '''<?xml version="1.0" encoding="utf-8"?>
<!-- Etapa futura. -->
<shape xmlns:android="http://schemas.android.com/apk/res/android" android:shape="oval">
    <solid android:color="#FFDDE3EA" />
</shape>''')
    for kind, color in (("info", "#FFDCEBFF"), ("success", "#FFE8F5E9"), ("warning", "#FFFFF8E1"), ("error", "#FFFDE7E9")):
        ctx.add_res(f"drawable/bg_alert_{kind}.xml", f'''<?xml version="1.0" encoding="utf-8"?>
<!-- Fundo da caixa de aviso ({kind}). -->
<shape xmlns:android="http://schemas.android.com/apk/res/android" android:shape="rectangle">
    <corners android:radius="12dp" />
    <solid android:color="{color}" />
</shape>''')
    used_icons = {s.icon for s in p.screens if s.in_nav} | {"add"}
    for screen in p.screens:
        for comp in screen.components:
            if comp.type == "fab":
                used_icons.add(comp.props.get("icon", "add"))
    for icon in sorted(used_icons):
        data = ICONS.get(icon, ICONS["info"])[1]
        ctx.add_res(f"drawable/ic_nav_{icon}.xml", vector(data, "#FF000000", comment=f"Icone '{icon}'."))
    nav_screens = [s for s in p.screens if s.in_nav]
    if p.navigation == "bottom":
        nav_screens = nav_screens[:5]
    if p.navigation in ("bottom", "drawer") and nav_screens:
        items = []
        for screen in nav_screens:
            name = ctx.string(f"nav_{screen.name}", screen.title or screen.name)
            items.append(f'''    <item
        android:id="@+id/nav_{ctx.screen_route(screen)}"
        android:icon="@drawable/ic_nav_{screen.icon if screen.icon in ICONS else "info"}"
        android:title="@string/{name}" />''')
        menu = "bottom_nav" if p.navigation == "bottom" else "drawer_nav"
        ctx.add_res(f"menu/{menu}.xml", f'''<?xml version="1.0" encoding="utf-8"?>
<!-- Itens do menu de navegacao principal. -->
<menu xmlns:android="http://schemas.android.com/apk/res/android">
{chr(10).join(items)}
</menu>''')


def write_strings(ctx):
    """Grava strings.xml (e copias para os demais idiomas) depois da geracao das telas."""
    p = ctx.project
    ctx.strings = {"app_name": p.name, **{k: v for k, v in ctx.strings.items() if k != "app_name"}}
    ctx.add_res("values/strings.xml", ctx.strings_xml("Textos do aplicativo. Traduza em values-xx/strings.xml."))
    primary = (p.languages or ["pt"])[0]
    for lang in (p.languages or [])[1:]:
        folder = {"pt": "pt", "en": "en", "es": "es", "fr": "fr", "de": "de", "it": "it"}.get(lang, lang)
        if folder == primary:
            continue
        ctx.add_res(f"values-{folder}/strings.xml",
                    ctx.strings_xml(f"Traducao para '{lang}'. Os textos abaixo sao uma copia: traduza cada um."))


__all__ = ["generate", "write_strings", "mix", "xml_escape"]
