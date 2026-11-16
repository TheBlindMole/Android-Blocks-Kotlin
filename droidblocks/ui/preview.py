"""Previa visual (aproximada) das telas no celular do editor.

Desenha cada bloco parecido com o resultado no aplicativo, em vez das pecas de
quebra-cabeca. As medidas sao aproximadas: o objetivo e dar uma nocao do layout.
"""

import math
import tkinter.font as tkfont

from ..core.generator.screen_spec import options_of

BG = "#F6F8FC"
SURFACE = "#FFFFFF"
SURFACE_VARIANT = "#E3E8EF"
ON_SURFACE = "#1A1C1E"
MUTED = "#5F6670"
OUTLINE = "#C3C8D0"

_FONTS = {}


def font(size, weight="normal", slant="roman"):
    key = (size, weight, slant)
    if key not in _FONTS:
        _FONTS[key] = tkfont.Font(family="Helvetica", size=size, weight=weight, slant=slant)
    return _FONTS[key]


def text_height(text, fnt, width):
    """Altura aproximada de um texto quebrado em linhas na largura dada."""
    if not text:
        return fnt.metrics("linespace")
    lines = 0
    for paragraph in str(text).split("\n"):
        lines += max(1, math.ceil(fnt.measure(paragraph) / max(1, width)))
    return lines * fnt.metrics("linespace")


def sample_items(project, source, count=3):
    """Itens para ilustrar listas: dados de exemplo do projeto ou genericos."""
    source = str(source or "")
    if source.startswith("sample:"):
        rows = project.samples.get(source[7:]) or project.samples.get("default") or []
        if rows:
            return [(r.get("title", ""), r.get("subtitle", ""), r.get("price")) for r in rows[:count]]
    label = {"cart": "Item do carrinho", "favorites": "Favorito", "chat": "Mensagem", "contacts": "Contato"}.get(
        source, source.split(":")[-1].split(".")[-1] or "Item")
    return [(f"{label} {i + 1}", "Descrição do item", 19.9 * (i + 1)) for i in range(count)]


def price_text(value):
    if value in (None, ""):
        return ""
    try:
        return "R$ " + f"{float(value):,.2f}".replace(",", "X").replace(".", ",").replace("X", ".")
    except (TypeError, ValueError):
        return str(value)


def block_height(comp, project, width):
    """Altura em pixels que o bloco ocupa na previa."""
    p = comp.props
    tp = comp.type
    num = lambda key, default: _int(p.get(key), default)  # noqa: E731
    if tp == "title":
        size = {"large": 18, "medium": 15, "small": 12}.get(p.get("size"), 18)
        return text_height(p.get("text"), font(size, "bold"), width) + 4
    if tp == "text":
        return text_height(p.get("text"), font(10), width) + 2
    if tp in ("button", "button_row", "social_links", "search_bar"):
        return 38
    if tp in ("text_field", "dropdown", "date_picker"):
        return 46
    if tp in ("checkbox", "switch", "stepper", "tags", "chips", "tabs"):
        return 32
    if tp == "slider":
        return 44
    if tp == "radio_group":
        return 20 + 24 * len(options_of(comp))
    if tp == "rating":
        return 44
    if tp in ("image", "web_view", "map_view", "video_player", "camera_preview", "lottie", "signature"):
        return max(60, min(200, int(num("height", 180) * 0.75))) + (22 if tp == "signature" else 0)
    if tp == "card":
        return 24 + text_height(p.get("body"), font(9), width - 24) + 18
    if tp == "banner":
        return 84
    if tp == "list":
        return 3 * 54
    if tp == "grid":
        return 2 * 118
    if tp == "carousel":
        return max(90, min(180, int(num("height", 180) * 0.7)))
    if tp == "h_list":
        return 116
    if tp == "item_detail":
        return 210
    if tp == "stat_card":
        return 60
    if tp == "chart":
        return 120
    if tp == "cart_summary":
        return 78
    if tp == "avatar":
        return 64
    if tp == "divider":
        return 9
    if tp == "spacer":
        return max(4, int(num("height", 16) * 0.75))
    if tp == "progress":
        return 12
    if tp == "qr_code":
        return 120
    if tp == "timer":
        return 70
    if tp == "calendar":
        return 170
    if tp == "expandable":
        return 44
    if tp == "key_value":
        rows = [r for r in str(p.get("rows", "")).splitlines() if r.strip()]
        return 20 + (20 if p.get("title") else 0) + 20 * len(rows)
    if tp == "steps":
        return 54
    if tp == "alert":
        return text_height(p.get("text"), font(9), width - 24) + 22
    if tp == "quote":
        return text_height(p.get("text"), font(10, slant="italic"), width - 28) + (40 if p.get("author") else 24)
    if tp == "price_tag":
        return 54
    return 40


def _int(value, default):
    try:
        return int(float(value))
    except (TypeError, ValueError):
        return default


def _shorten(text, fnt, width):
    text = str(text or "")
    if fnt.measure(text) <= width:
        return text
    while text and fnt.measure(text + "...") > width:
        text = text[:-1]
    return text + "..."


def _rrect(cv, x0, y0, x1, y1, r, **kw):
    r = max(0, min(r, (x1 - x0) / 2, (y1 - y0) / 2))
    points = [x0 + r, y0, x1 - r, y0, x1, y0, x1, y0 + r, x1, y1 - r, x1, y1, x1 - r, y1,
              x0 + r, y1, x0, y1, x0, y1 - r, x0, y0 + r, x0, y0]
    return cv.create_polygon(points, smooth=True, **kw)


def draw_block(cv, comp, project, x0, y0, x1, y1, tags, primary):
    """Desenha um bloco na area (x0, y0)-(x1, y1)."""
    p = comp.props
    tp = comp.type
    w = x1 - x0
    kw = {"tags": tags}

    def label(x, y, text, size=10, color=ON_SURFACE, weight="normal", anchor="w", width=None, slant="roman"):
        fnt = font(size, weight, slant)
        if width is None:
            text = _shorten(text, fnt, x1 - x - 4 if anchor == "w" else w)
            return cv.create_text(x, y, text=text, fill=color, font=fnt, anchor=anchor, **kw)
        return cv.create_text(x, y, text=text, fill=color, font=fnt, anchor=anchor, width=width, **kw)

    # Fundo transparente clicavel para selecionar o bloco.
    cv.create_rectangle(x0, y0, x1, y1, fill=BG, outline="", **kw)

    if tp == "title":
        size = {"large": 18, "medium": 15, "small": 12}.get(p.get("size"), 18)
        anchor = {"center": "n", "end": "ne"}.get(p.get("align"), "nw")
        x = {"n": (x0 + x1) / 2, "ne": x1}.get(anchor, x0)
        cv.create_text(x, y0, text=p.get("text", ""), font=font(size, "bold"), fill=ON_SURFACE, anchor=anchor,
                       width=w, justify={"n": "center", "ne": "right"}.get(anchor, "left"), **kw)
    elif tp == "text":
        anchor = {"center": "n", "end": "ne"}.get(p.get("align"), "nw")
        x = {"n": (x0 + x1) / 2, "ne": x1}.get(anchor, x0)
        color = MUTED if p.get("style") == "caption" else ON_SURFACE
        cv.create_text(x, y0, text=p.get("text", ""), font=font(10), fill=color, anchor=anchor, width=w,
                       justify={"n": "center", "ne": "right"}.get(anchor, "left"), **kw)
    elif tp == "button":
        _button(cv, x0, y0 + 3, x1, y1 - 3, p.get("text", ""), p.get("style", "filled"), primary, kw)
    elif tp == "button_row":
        mid = (x0 + x1) / 2
        _button(cv, x0, y0 + 3, mid - 4, y1 - 3, p.get("text1", ""), "outlined", primary, kw)
        _button(cv, mid + 4, y0 + 3, x1, y1 - 3, p.get("text2", ""), "filled", primary, kw)
    elif tp in ("text_field", "dropdown", "date_picker"):
        _rrect(cv, x0, y0 + 4, x1, y1 - 2, 6, fill=SURFACE, outline=OUTLINE, **kw)
        label(x0 + 12, y0 + 6 + (y1 - y0 - 8) / 2, p.get("label", ""), 10, MUTED)
        if tp == "dropdown":
            label(x1 - 12, (y0 + y1) / 2 + 1, "v", 9, MUTED, anchor="e")
        if tp == "date_picker":
            label(x1 - 12, (y0 + y1) / 2 + 1, "[ ]", 9, MUTED, anchor="e")
    elif tp == "search_bar":
        _rrect(cv, x0, y0 + 2, x1, y1 - 2, 18, fill=SURFACE_VARIANT, outline="", **kw)
        label(x0 + 16, (y0 + y1) / 2, p.get("hint", "Buscar"), 10, MUTED)
    elif tp in ("checkbox", "switch"):
        cy = (y0 + y1) / 2
        if tp == "checkbox":
            cv.create_rectangle(x0 + 2, cy - 8, x0 + 18, cy + 8, outline=MUTED, width=2, **kw)
            label(x0 + 28, cy, p.get("label", ""))
        else:
            label(x0, cy, p.get("label", ""))
            _rrect(cv, x1 - 40, cy - 10, x1, cy + 10, 10, fill=SURFACE_VARIANT, outline=MUTED, **kw)
            cv.create_oval(x1 - 36, cy - 6, x1 - 24, cy + 6, fill=MUTED, outline="", **kw)
    elif tp == "slider":
        label(x0, y0 + 10, p.get("label", ""), 9, MUTED)
        cy = y0 + 30
        cv.create_line(x0 + 4, cy, x1 - 4, cy, fill=SURFACE_VARIANT, width=4, **kw)
        cv.create_line(x0 + 4, cy, x0 + w * 0.4, cy, fill=primary, width=4, **kw)
        cv.create_oval(x0 + w * 0.4 - 8, cy - 8, x0 + w * 0.4 + 8, cy + 8, fill=primary, outline="", **kw)
    elif tp == "radio_group":
        label(x0, y0 + 9, p.get("label", ""), 9, MUTED)
        for i, option in enumerate(options_of(comp)):
            cy = y0 + 30 + i * 24
            cv.create_oval(x0 + 2, cy - 7, x0 + 16, cy + 7, outline=primary if i == 0 else MUTED, width=2, **kw)
            if i == 0:
                cv.create_oval(x0 + 6, cy - 3, x0 + 12, cy + 3, fill=primary, outline="", **kw)
            label(x0 + 26, cy, option)
    elif tp in ("chips", "tags", "tabs"):
        x = x0
        cy = (y0 + y1) / 2
        for i, option in enumerate(options_of(comp)):
            tw = font(9).measure(option) + 22
            if x + tw > x1:
                break
            if tp == "tabs":
                active = i == 0
                label(x + tw / 2, cy, option, 9, primary if active else MUTED, "bold" if active else "normal", "center")
                if active:
                    cv.create_line(x + 4, y1 - 2, x + tw - 4, y1 - 2, fill=primary, width=3, **kw)
            else:
                fill = "#DCE6F5" if tp == "tags" else (primary if i == 0 else SURFACE)
                color = "#FFFFFF" if (tp == "chips" and i == 0) else ON_SURFACE
                _rrect(cv, x, cy - 13, x + tw, cy + 13, 8, fill=fill, outline=OUTLINE if tp == "chips" else "", **kw)
                label(x + tw / 2, cy, option, 9, color, anchor="center")
            x += tw + 6
    elif tp == "rating":
        label(x0, y0 + 9, p.get("label", ""), 9, MUTED)
        for i in range(_int(p.get("max"), 5)):
            label(x0 + 2 + i * 22, y0 + 30, "*" if i < 3 else "o", 14, "#F5A623" if i < 3 else MUTED)
    elif tp == "stepper":
        cy = (y0 + y1) / 2
        label(x0, cy, p.get("label", ""))
        for dx, sign in ((-84, "-"), (-24, "+")):
            cv.create_oval(x1 + dx, cy - 12, x1 + dx + 24, cy + 12, outline=OUTLINE, **kw)
            label(x1 + dx + 12, cy, sign, 11, primary, "bold", "center")
        label(x1 - 42, cy, "1", 11, ON_SURFACE, "bold", "center")
    elif tp in ("image", "web_view", "map_view", "video_player", "camera_preview", "lottie"):
        names = {"image": "Imagem", "web_view": "Página web", "map_view": "Mapa", "video_player": "Vídeo",
                 "camera_preview": "Câmera", "lottie": "Animação"}
        fill = {"map_view": "#D7E8D0", "video_player": "#20242B", "camera_preview": "#20242B"}.get(tp, SURFACE_VARIANT)
        _rrect(cv, x0, y0, x1, y1, 10, fill=fill, outline="", **kw)
        color = "#FFFFFF" if tp in ("video_player", "camera_preview") else MUTED
        text = "|>  " + names[tp] if tp == "video_player" else names[tp]
        label((x0 + x1) / 2, (y0 + y1) / 2, text, 10, color, anchor="center")
    elif tp == "signature":
        label(x0, y0 + 9, p.get("label", ""), 10, ON_SURFACE, "bold")
        label(x1, y0 + 9, "Limpar", 9, primary, anchor="e")
        _rrect(cv, x0, y0 + 22, x1, y1, 10, fill=SURFACE_VARIANT, outline="", **kw)
        mid = (y0 + 22 + y1) / 2
        cv.create_line(x0 + 30, mid + 10, x0 + 60, mid - 14, x0 + 80, mid + 12, x0 + 110, mid - 8, x0 + 140, mid + 6,
                       smooth=True, fill=ON_SURFACE, width=2, **kw)
    elif tp in ("card", "expandable", "quote", "key_value", "stat_card", "cart_summary", "item_detail", "timer",
                "calendar", "price_tag", "avatar", "qr_code", "chart"):
        _card_like(cv, comp, project, x0, y0, x1, y1, kw, primary, label)
    elif tp == "banner":
        _rrect(cv, x0, y0, x1, y1, 12, fill=primary, outline="", **kw)
        label(x0 + 16, y0 + 30, p.get("title", ""), 14, "#FFFFFF", "bold")
        label(x0 + 16, y0 + 54, p.get("subtitle", ""), 9, "#E6EEFF")
    elif tp == "list":
        for i, (title, subtitle, price) in enumerate(sample_items(project, p.get("source"))):
            top = y0 + i * 54
            if p.get("show_image", True):
                _rrect(cv, x0, top + 6, x0 + 42, top + 48, 8, fill=SURFACE_VARIANT, outline="", **kw)
                tx = x0 + 52
            else:
                tx = x0 + 4
            label(tx, top + 18, title, 10, ON_SURFACE, "bold")
            label(tx, top + 36, subtitle, 9, MUTED)
            if p.get("show_price") and price is not None:
                label(x1 - 2, top + 18, price_text(price), 9, primary, "bold", "e")
            cv.create_line(tx, top + 53, x1, top + 53, fill=SURFACE_VARIANT, **kw)
    elif tp in ("grid", "h_list", "carousel"):
        _cards(cv, comp, project, x0, y0, x1, y1, kw, primary, label)
    elif tp == "divider":
        cv.create_line(x0, (y0 + y1) / 2, x1, (y0 + y1) / 2, fill=OUTLINE, **kw)
    elif tp == "spacer":
        pass
    elif tp == "progress":
        cv.create_line(x0, (y0 + y1) / 2, x1, (y0 + y1) / 2, fill=SURFACE_VARIANT, width=4, **kw)
        cv.create_line(x0, (y0 + y1) / 2, x0 + w * 0.35, (y0 + y1) / 2, fill=primary, width=4, **kw)
    elif tp == "steps":
        options = options_of(comp) or ["1"]
        current = _int(p.get("current"), 1)
        step = w / len(options)
        for i, option in enumerate(options):
            cx = x0 + step * i + step / 2
            done = i < current
            cv.create_oval(cx - 13, y0 + 4, cx + 13, y0 + 30, fill=primary if done else SURFACE_VARIANT,
                           outline="", **kw)
            label(cx, y0 + 17, str(i + 1), 9, "#FFFFFF" if done else MUTED, "bold", "center")
            fnt = font(8)
            cv.create_text(cx, y0 + 42, text=_shorten(option, fnt, step - 4), font=fnt, fill=MUTED, **kw)
    elif tp == "alert":
        colors = {"success": ("#E8F5E9", "#1B5E20"), "warning": ("#FFF8E1", "#7A5900"),
                  "error": ("#FDE7E9", "#8C1D18")}.get(p.get("kind"), ("#DCEBFF", "#0D3B66"))
        _rrect(cv, x0, y0, x1, y1, 10, fill=colors[0], outline="", **kw)
        cv.create_text(x0 + 12, y0 + 11, text=p.get("text", ""), font=font(9), fill=colors[1], anchor="nw",
                       width=w - 24, **kw)
    elif tp == "social_links":
        names = [n for n, k in (("WhatsApp", "whatsapp"), ("Instagram", "instagram"), ("Site", "website")) if p.get(k)]
        if names:
            step = w / len(names)
            for i, name in enumerate(names):
                _button(cv, x0 + step * i + (3 if i else 0), y0 + 3, x0 + step * (i + 1) - 3, y1 - 3, name,
                        "outlined", primary, kw)
    elif tp == "fab":
        pass
    else:
        _rrect(cv, x0, y0, x1, y1, 8, fill=SURFACE, outline=OUTLINE, **kw)
        label(x0 + 12, (y0 + y1) / 2, tp, 9, MUTED)


def _button(cv, x0, y0, x1, y1, text, style, primary, kw):
    fnt = font(10, "bold")
    text = _shorten(text, fnt, x1 - x0 - 12)
    cx, cy = (x0 + x1) / 2, (y0 + y1) / 2
    if style == "text":
        cv.create_text(cx, cy, text=text, fill=primary, font=fnt, **kw)
        return
    if style == "outlined":
        _rrect(cv, x0, y0, x1, y1, 16, fill=BG, outline=OUTLINE, **kw)
        cv.create_text(cx, cy, text=text, fill=primary, font=fnt, **kw)
        return
    fill = "#DCE6F5" if style == "tonal" else primary
    _rrect(cv, x0, y0, x1, y1, 16, fill=fill, outline="", **kw)
    cv.create_text(cx, cy, text=text, fill=ON_SURFACE if style == "tonal" else "#FFFFFF", font=fnt, **kw)


def _card_like(cv, comp, project, x0, y0, x1, y1, kw, primary, label):
    p = comp.props
    tp = comp.type
    w = x1 - x0
    if tp not in ("price_tag", "avatar", "qr_code", "timer"):
        _rrect(cv, x0, y0, x1, y1, 10, fill=SURFACE, outline=SURFACE_VARIANT, **kw)
    if tp == "card":
        label(x0 + 12, y0 + 16, p.get("title", ""), 11, ON_SURFACE, "bold")
        cv.create_text(x0 + 12, y0 + 30, text=p.get("body", ""), font=font(9), fill=MUTED, anchor="nw",
                       width=w - 24, **kw)
    elif tp == "expandable":
        label(x0 + 12, (y0 + y1) / 2, p.get("title", ""), 10, ON_SURFACE, "bold")
        label(x1 - 12, (y0 + y1) / 2, "+", 13, primary, "bold", "e")
    elif tp == "quote":
        cv.create_text(x0 + 14, y0 + 12, text=f"“{p.get('text', '')}”", font=font(10, slant="italic"),
                       fill=ON_SURFACE, anchor="nw", width=w - 28, **kw)
        if p.get("author"):
            label(x0 + 14, y1 - 14, "- " + p.get("author"), 9, primary, "bold")
    elif tp == "key_value":
        y = y0 + 14
        if p.get("title"):
            label(x0 + 12, y, p.get("title"), 10, ON_SURFACE, "bold")
            y += 20
        for row in [r for r in str(p.get("rows", "")).splitlines() if r.strip()]:
            name, _, value = row.partition(":")
            label(x0 + 12, y, name.strip(), 9, MUTED)
            label(x1 - 12, y, value.strip(), 9, ON_SURFACE, "bold", "e")
            y += 20
    elif tp == "stat_card":
        label(x0 + 12, y0 + 18, p.get("label", ""), 9, MUTED)
        label(x0 + 12, y0 + 40, p.get("value", ""), 15, primary, "bold")
    elif tp == "cart_summary":
        label(x0 + 12, y0 + 18, "Total", 10, MUTED)
        label(x1 - 12, y0 + 18, "R$ 0,00", 12, ON_SURFACE, "bold", "e")
        _button(cv, x0 + 12, y0 + 36, x1 - 12, y1 - 8, p.get("button", "Finalizar"), "filled", primary, kw)
    elif tp == "item_detail":
        title, subtitle, price = sample_items(project, "sample:default", 1)[0]
        if p.get("show_image", True):
            _rrect(cv, x0 + 8, y0 + 8, x1 - 8, y0 + 120, 8, fill=SURFACE_VARIANT, outline="", **kw)
            label((x0 + x1) / 2, y0 + 64, "Imagem do item", 9, MUTED, anchor="center")
        label(x0 + 12, y0 + 140, title + " (item escolhido)", 12, ON_SURFACE, "bold")
        label(x0 + 12, y0 + 162, subtitle, 9, MUTED)
        if p.get("show_price"):
            label(x0 + 12, y0 + 186, price_text(price), 12, primary, "bold")
    elif tp == "timer":
        label((x0 + x1) / 2, y0 + 26, "01:00", 22, ON_SURFACE, "bold", "center")
        label((x0 + x1) / 2, y0 + 56, "Iniciar   |   Zerar", 9, primary, anchor="center")
    elif tp == "calendar":
        label(x0 + 12, y0 + 14, "Novembro", 10, ON_SURFACE, "bold")
        for i in range(30):
            col, row = i % 7, i // 7
            cx = x0 + 20 + col * (w - 40) / 6
            if i == 13:
                cv.create_oval(cx - 11, y0 + 29 + row * 26, cx + 11, y0 + 51 + row * 26, fill=primary,
                               outline="", **kw)
            label(cx, y0 + 40 + row * 26, str(i + 1), 9, "#FFFFFF" if i == 13 else ON_SURFACE, anchor="center")
    elif tp == "price_tag":
        label(x0, y0 + 10, p.get("label", ""), 9, MUTED)
        value = p.get("value", "")
        fnt = font(17, "bold")
        cv.create_text(x0, y0 + 36, text=value, font=fnt, fill=primary, anchor="w", **kw)
        if p.get("old_value"):
            ox = x0 + fnt.measure(value) + 10
            old = cv.create_text(ox, y0 + 40, text=p.get("old_value"), font=font(10), fill=MUTED, anchor="w", **kw)
            bx0, by0, bx1, by1 = cv.bbox(old)
            cv.create_line(bx0, (by0 + by1) / 2, bx1, (by0 + by1) / 2, fill=MUTED, **kw)
    elif tp == "avatar":
        cv.create_oval(x0, y0 + 6, x0 + 52, y0 + 58, fill=primary, outline="", **kw)
        initial = (str(p.get("name", "U")) or "U")[0].upper()
        label(x0 + 26, y0 + 32, initial, 16, "#FFFFFF", "bold", "center")
        label(x0 + 64, y0 + 24, p.get("name", ""), 12, ON_SURFACE, "bold")
        label(x0 + 64, y0 + 44, p.get("subtitle", ""), 9, MUTED)
    elif tp == "qr_code":
        size = 110
        qx = (x0 + x1) / 2 - size / 2
        cv.create_rectangle(qx, y0 + 4, qx + size, y0 + 4 + size, fill="#FFFFFF", outline=OUTLINE, **kw)
        seed = sum(ord(c) for c in str(p.get("text", "")))
        cell = size / 11
        for i in range(11):
            for j in range(11):
                corner = (i < 3 and j < 3) or (i < 3 and j > 7) or (i > 7 and j < 3)
                if corner or (seed * (i + 3) * (j + 7)) % 5 < 2:
                    cv.create_rectangle(qx + i * cell, y0 + 4 + j * cell, qx + (i + 1) * cell,
                                        y0 + 4 + (j + 1) * cell, fill=ON_SURFACE, outline="", **kw)
    elif tp == "chart":
        values = [float(v) for v in str(p.get("values", "")).replace(";", ",").split(",") if _is_number(v)] or [1]
        top = max(values) or 1
        n = len(values)
        inner_w = w - 24
        if p.get("style") == "line":
            points = []
            for i, v in enumerate(values):
                points += [x0 + 12 + inner_w * i / max(1, n - 1), y1 - 12 - (y1 - y0 - 28) * v / top]
            if len(points) >= 4:
                cv.create_line(*points, fill=primary, width=2, smooth=True, **kw)
        else:
            bar = inner_w / n
            for i, v in enumerate(values):
                bx = x0 + 12 + i * bar
                cv.create_rectangle(bx + 3, y1 - 12 - (y1 - y0 - 28) * v / top, bx + bar - 3, y1 - 12,
                                    fill=primary, outline="", **kw)


def _is_number(value):
    try:
        float(value)
        return True
    except ValueError:
        return False


def _cards(cv, comp, project, x0, y0, x1, y1, kw, primary, label):
    p = comp.props
    tp = comp.type
    w = x1 - x0
    if tp == "grid":
        cols = max(1, min(4, _int(p.get("columns"), 2)))
        items = sample_items(project, p.get("source"), cols * 2)
        cw = (w - 8 * (cols - 1)) / cols
        for i, (title, subtitle, price) in enumerate(items):
            cx = x0 + (i % cols) * (cw + 8)
            cy = y0 + (i // cols) * 118
            _rrect(cv, cx, cy, cx + cw, cy + 110, 10, fill=SURFACE, outline=SURFACE_VARIANT, **kw)
            _rrect(cv, cx + 4, cy + 4, cx + cw - 4, cy + 62, 8, fill=SURFACE_VARIANT, outline="", **kw)
            fnt = font(9, "bold")
            cv.create_text(cx + 8, cy + 76, text=_shorten(title, fnt, cw - 16), font=fnt, fill=ON_SURFACE,
                           anchor="w", **kw)
            if p.get("show_price") and price is not None:
                cv.create_text(cx + 8, cy + 94, text=price_text(price), font=font(9, "bold"), fill=primary,
                               anchor="w", **kw)
    elif tp == "h_list":
        items = sample_items(project, p.get("source"), 4)
        for i, (title, subtitle, price) in enumerate(items):
            cx = x0 + i * 128
            if cx >= x1:
                break
            right = min(cx + 120, x1)
            _rrect(cv, cx, y0, right, y1 - 4, 10, fill=SURFACE, outline=SURFACE_VARIANT, **kw)
            _rrect(cv, cx + 4, y0 + 4, right - 4, y0 + 62, 8, fill=SURFACE_VARIANT, outline="", **kw)
            fnt = font(9, "bold")
            cv.create_text(cx + 8, y0 + 76, text=_shorten(title, fnt, right - cx - 16), font=fnt, fill=ON_SURFACE,
                           anchor="w", **kw)
            if p.get("show_price") and price is not None:
                cv.create_text(cx + 8, y0 + 94, text=price_text(price), font=font(9, "bold"), fill=primary,
                               anchor="w", **kw)
    else:
        items = sample_items(project, p.get("source"), 2)
        card_w = w * 0.82
        for i, (title, subtitle, _) in enumerate(items):
            cx = x0 + i * (card_w + 10)
            right = min(cx + card_w, x1)
            if right - cx < 20:
                break
            _rrect(cv, cx, y0, right, y1, 12, fill="#3A4A63" if i == 0 else "#55657F", outline="", **kw)
            fnt = font(11, "bold")
            cv.create_text(cx + 12, y1 - 30, text=_shorten(title, fnt, right - cx - 24), font=fnt, fill="#FFFFFF",
                           anchor="w", **kw)
            cv.create_text(cx + 12, y1 - 13, text=_shorten(subtitle, font(9), right - cx - 24), font=font(9),
                           fill="#E6EEFF", anchor="w", **kw)
