"""Area central: celular simulado onde os blocos da tela sao empilhados e reorganizados."""

import tkinter as tk
import tkinter.font as tkfont
from tkinter import ttk

from ..catalog.components import COMPONENTS, ACTIONS, LIST_COMPONENTS, parse_action, split_actions
from . import preview
from .theme import C, FONT, BLOCK_COLORS, bind_wheel
from .text import t

PHONE_W = 380
BLOCK_H = 50
LIST_H = 64
GAP = 8
PAD = 14


def _shorten(text, size=34):
    text = " ".join(str(text or "").split())
    return text if len(text) <= size else text[:size - 3] + "..."


def action_label(value, project=None):
    """Descricao curta de uma acao; em cadeias mostra a primeira e quantas vem depois."""
    parts = split_actions(value)
    if not parts:
        return ""
    key, arg = parse_action(parts[0])
    if key not in ACTIONS or key == "none":
        return ""
    label = t(ACTIONS[key].label)
    text = f"{label}: {_shorten(arg, 18)}" if arg else label
    if len(parts) > 1:
        text += f"  +{len(parts) - 1}"
    return text


def source_label(source):
    if not source:
        return "exemplo"
    if source.startswith("sample:"):
        return "Exemplo: " + source[7:]
    if source.startswith("entity:"):
        return "Banco: " + source[7:]
    if source.startswith("api:"):
        return "API: " + source[4:]
    return {"cart": "Carrinho", "favorites": "Favoritos", "chat": "Chat", "contacts": "Contatos"}.get(source, source)


def summary(comp):
    """Resumo de uma linha exibido no bloco."""
    p = comp.props
    tp = comp.type
    if tp in ("title", "text"):
        return f'"{_shorten(p.get("text"))}"'
    if tp == "button":
        act = action_label(p.get("action"))
        return f'"{_shorten(p.get("text"), 16)}"' + (f"  ->  {act}" if act else "")
    if tp in ("card", "banner"):
        return _shorten(p.get("title"))
    if tp == "text_field":
        rule = p.get("validation", "none")
        return f'{_shorten(p.get("label"), 16)}  [{p.get("key")}]' + (f"  regra: {rule}" if rule != "none" else "")
    if tp in ("checkbox", "switch", "slider", "radio_group", "dropdown", "date_picker", "rating", "stepper"):
        return f'{_shorten(p.get("label"), 20)}  [{p.get("key")}]'
    if tp in ("chips", "tabs"):
        return _shorten(p.get("options"))
    if tp in LIST_COMPONENTS:
        act = action_label(p.get("item_action"))
        return source_label(p.get("source")) + (f"  ->  {act}" if act else "")
    if tp == "search_bar":
        return _shorten(p.get("hint"))
    if tp == "image":
        return "Foto tirada/escolhida" if p.get("source") == "photo" else _shorten(p.get("url"))
    if tp == "stat_card":
        return f'{_shorten(p.get("label"), 16)}: {p.get("value")}'
    if tp == "chart":
        return f'{p.get("style")}: {_shorten(p.get("values"), 24)}'
    if tp in ("web_view", "video_player", "lottie"):
        return _shorten(p.get("url"))
    if tp == "map_view":
        return f'{p.get("lat")}, {p.get("lng")}'
    if tp == "qr_code":
        return _shorten(p.get("text"))
    if tp == "timer":
        return "Contagem regressiva" if p.get("mode") == "countdown" else "Cronometro"
    if tp == "avatar":
        return _shorten(p.get("name"))
    if tp == "fab":
        return action_label(p.get("action"))
    if tp == "cart_summary":
        return action_label(p.get("action"))
    if tp == "spacer":
        return f'{p.get("height")} dp'
    if tp == "expandable":
        return _shorten(p.get("title"))
    if tp == "key_value":
        rows = [r for r in str(p.get("rows", "")).splitlines() if r.strip()]
        return f'{_shorten(p.get("title"), 20)}  ({len(rows)} linhas)'
    if tp == "steps":
        return f'etapa {p.get("current")} de: {_shorten(p.get("options"), 24)}'
    if tp == "alert":
        return f'[{p.get("kind")}] {_shorten(p.get("text"), 26)}'
    if tp == "button_row":
        return f'"{_shorten(p.get("text1"), 10)}" | "{_shorten(p.get("text2"), 10)}"'
    if tp in ("signature",):
        return _shorten(p.get("label"))
    if tp == "quote":
        return f'"{_shorten(p.get("text"), 26)}"'
    if tp == "tags":
        return _shorten(p.get("options"))
    if tp == "price_tag":
        old = p.get("old_value")
        return f'{p.get("value")}' + (f'  (de {old})' if old else "")
    if tp == "social_links":
        names = [n for n, k in (("WhatsApp", "whatsapp"), ("Instagram", "instagram"), ("Site", "website")) if p.get(k)]
        return ", ".join(names)
    return ""


class ScreenCanvas(ttk.Frame):
    """Desenha a tela atual como um celular com blocos encaixados."""

    def __init__(self, master, app):
        super().__init__(master, style="Bg.TFrame")
        self.app = app
        self.canvas = tk.Canvas(self, bg=C["bg"], highlightthickness=0, bd=0)
        scroll = ttk.Scrollbar(self, orient="vertical", command=self.canvas.yview)
        self.canvas.configure(yscrollcommand=scroll.set)
        self.canvas.pack(side="left", fill="both", expand=True)
        scroll.pack(side="right", fill="y")
        bind_wheel(self.canvas, self.canvas)
        self.positions = []
        self.drag = None
        self.insert_line = None
        self.phone_box = (0, 0, 0, 0)
        # False: blocos de montagem; True: previa parecida com o app final.
        self.preview = False
        self.canvas.bind("<Configure>", lambda e: self.redraw())
        self.canvas.bind("<ButtonPress-1>", self._press)
        self.canvas.bind("<B1-Motion>", self._motion)
        self.canvas.bind("<ButtonRelease-1>", self._release)
        self.canvas.bind("<Double-Button-1>", self._double)
        self.canvas.bind("<Button-3>", self._context)
        self.canvas.bind("<Button-2>", self._context)

    # ------------------------------------------------------------ desenho

    def redraw(self):
        cv = self.canvas
        cv.delete("all")
        project = self.app.project
        screen = self.app.current_screen()
        width = max(cv.winfo_width(), PHONE_W + 40)
        x0 = (width - PHONE_W) // 2
        x1 = x0 + PHONE_W
        y = 24
        self.positions = []
        if screen is None:
            cv.create_text(width // 2, 80, text="Nenhuma tela. Use '+ Tela' para criar.", fill=C["muted"],
                           font=FONT["h2"])
            return
        comps = [c for c in screen.components if c.type in COMPONENTS]
        if self.preview:
            inner = PHONE_W - 2 * PAD
            heights = [0 if c.type == "fab" else preview.block_height(c, project, inner) for c in comps]
        else:
            heights = [LIST_H if c.type in ("list", "grid", "carousel", "h_list", "signature", "item_detail", "chart",
                                            "map_view", "video_player", "web_view", "camera_preview", "image")
                       else BLOCK_H for c in comps]
        content_h = sum(heights) + (10 if self.preview else GAP) * max(0, len(comps) - 1)
        in_bottom = project.navigation == "bottom" and screen.in_nav
        phone_h = max(560, 120 + content_h + 60 + (56 if in_bottom else 0))
        # Corpo do celular
        self._round_rect(x0 - 10, y - 10, x1 + 10, y + phone_h + 10, 34, fill=C["phone"], outline=C["border"])
        self._round_rect(x0, y, x1, y + phone_h, 26, fill=preview.BG if self.preview else C["phone_screen"], outline="")
        cv.create_oval(width // 2 - 4, y + 8, width // 2 + 4, y + 16, fill="#1A2333", outline="")
        # Barra superior do app
        primary = project.primary_color or C["accent"]
        top = y + 26
        cv.create_rectangle(x0, top, x1, top + 52, fill=primary, outline="")
        start = project.get_start_screen()
        prefix = ""
        if screen is not start and not screen.in_nav:
            prefix = "<-  "
        elif project.navigation == "drawer":
            prefix = "=  "
        cv.create_text(x0 + 16, top + 26, anchor="w", text=prefix + (screen.title or screen.name),
                       fill="#FFFFFF", font=FONT["h2"])
        if screen is start:
            cv.create_text(x1 - 12, top + 26, anchor="e", text="inicial", fill="#DDE8FF", font=FONT["small"])
        # Blocos
        by = top + 52 + PAD
        bx0, bx1 = x0 + PAD, x1 - PAD
        self.phone_box = (x0, y, x1, y + phone_h)
        if not comps:
            cv.create_rectangle(bx0, by, bx1, by + 160, outline=C["border"], dash=(4, 3))
            cv.create_text((bx0 + bx1) // 2, by + 70, text="Arraste blocos da paleta para ca", fill=C["muted"],
                           font=FONT["base"])
            cv.create_text((bx0 + bx1) // 2, by + 92, text="ou de um duplo clique em um bloco", fill=C["dim"],
                           font=FONT["small"])
        gap = 10 if self.preview else GAP
        for comp, h in zip(comps, heights):
            if self.preview:
                if comp.type == "fab":
                    # O FAB flutua sobre a tela; fica na lista de posicoes so para manter os indices.
                    self.positions.append((comp.id, by, by))
                    continue
                tag = f"block:{comp.id}"
                preview.draw_block(cv, comp, project, bx0, by, bx1, by + h, (tag, "block"), primary)
                if comp.id == self.app.selected_id:
                    cv.create_rectangle(bx0 - 4, by - 4, bx1 + 4, by + h + 4, outline=C["accent"], width=2,
                                        dash=(5, 3), tags=(tag, "block"))
            else:
                self._block(comp, bx0, by, bx1, by + h)
            self.positions.append((comp.id, by, by + h))
            by += h + gap
        if in_bottom:
            self._bottom_nav(project, screen, x0, y + phone_h - 56, x1, y + phone_h)
        fabs = [c for c in comps if c.type == "fab"]
        if fabs:
            fy = y + phone_h - (76 if in_bottom else 20) - 46
            tag = (f"block:{fabs[0].id}", "block")
            cv.create_oval(x1 - 66, fy, x1 - 20, fy + 46, fill=primary, outline="", tags=tag)
            cv.create_text(x1 - 43, fy + 23, text="+", fill="#FFFFFF", font=FONT["title"], tags=tag)

        cv.configure(scrollregion=(0, 0, width, y + phone_h + 40))

    def _bottom_nav(self, project, screen, x0, y0, x1, y1):
        cv = self.canvas
        cv.create_rectangle(x0, y0, x1, y1, fill="#EEF2F8" if self.preview else "#121B29", outline="")
        items = [s for s in project.screens if s.in_nav][:5]
        if not items:
            return
        step = (x1 - x0) / len(items)
        for i, s in enumerate(items):
            cx = x0 + step * i + step / 2
            active = s is screen
            color = project.primary_color if active else C["muted"]
            cv.create_oval(cx - 5, y0 + 12, cx + 5, y0 + 22, fill=color, outline="")
            cv.create_text(cx, y0 + 38, text=_shorten(s.title or s.name, 12), fill=color, font=FONT["small"])

    def _block(self, comp, x0, y0, x1, y1):
        cv = self.canvas
        spec = COMPONENTS[comp.type]
        color = BLOCK_COLORS.get(spec.category, C["accent"])
        selected = comp.id == self.app.selected_id
        tag = f"block:{comp.id}"
        n0, n1 = x0 + 16, x0 + 36
        points = [x0, y0, n0, y0, n0 + 4, y0 + 5, n1 - 4, y0 + 5, n1, y0, x1, y0, x1, y1,
                  n1, y1, n1 - 4, y1 + 5, n0 + 4, y1 + 5, n0, y1, x0, y1]
        cv.create_polygon(points, fill=color, outline="#FFFFFF" if selected else self._shade(color, -0.35),
                          width=2 if selected else 1, tags=(tag, "block"))
        cv.create_rectangle(x0 + 8, y0 + 9, x0 + 52, y1 - 9, fill=self._shade(color, -0.3), outline="",
                            tags=(tag, "block"))
        cv.create_text(x0 + 30, (y0 + y1) / 2, text=spec.glyph, fill="#FFFFFF", font=FONT["block_small"],
                       tags=(tag, "block"))
        label = t(spec.label)
        sub = self._fit(t(summary(comp)), FONT["block_small"], x1 - x0 - 72)
        if sub:
            cv.create_text(x0 + 62, y0 + 16, anchor="w", text=label, fill="#FFFFFF", font=FONT["block"],
                           tags=(tag, "block"))
            cv.create_text(x0 + 62, y0 + 34, anchor="w", text=sub, fill="#E3ECFF", font=FONT["block_small"],
                           tags=(tag, "block"))
        else:
            cv.create_text(x0 + 62, (y0 + y1) / 2, anchor="w", text=label, fill="#FFFFFF", font=FONT["block"],
                           tags=(tag, "block"))

    _fonts = {}

    def _fit(self, text, font, max_px):
        """Corta o texto para caber na largura do bloco."""
        if not text:
            return text
        key = tuple(font)
        measure = self._fonts.get(key)
        if measure is None:
            measure = self._fonts[key] = tkfont.Font(family=font[0], size=font[1])
        if measure.measure(text) <= max_px:
            return text
        while text and measure.measure(text + "...") > max_px:
            text = text[:-1]
        return text.rstrip() + "..."

    @staticmethod
    def _shade(color, amount):
        color = color.lstrip("#")
        rgb = [int(color[i:i + 2], 16) for i in (0, 2, 4)]
        if amount < 0:
            rgb = [int(c * (1 + amount)) for c in rgb]
        else:
            rgb = [int(c + (255 - c) * amount) for c in rgb]
        return "#%02X%02X%02X" % tuple(max(0, min(255, c)) for c in rgb)

    def _round_rect(self, x0, y0, x1, y1, r, **kwargs):
        points = [x0 + r, y0, x1 - r, y0, x1, y0, x1, y0 + r, x1, y1 - r, x1, y1, x1 - r, y1,
                  x0 + r, y1, x0, y1, x0, y1 - r, x0, y0 + r, x0, y0]
        return self.canvas.create_polygon(points, smooth=True, **kwargs)

    # ------------------------------------------------------------ posicoes

    def block_at(self, cy):
        for cid, top, bottom in self.positions:
            if top <= cy <= bottom:
                return cid
        return None

    def index_at(self, cy):
        """Indice de insercao para uma coordenada y do canvas."""
        for index, (_, top, bottom) in enumerate(self.positions):
            if cy < (top + bottom) / 2:
                return index
        return len(self.positions)

    def _gap_y(self, index):
        if not self.positions:
            return self.phone_box[1] + 26 + 52 + PAD
        if index < len(self.positions):
            return self.positions[index][1] - GAP / 2
        return self.positions[-1][2] + GAP / 2

    def show_insert(self, index):
        self.hide_insert()
        y = self._gap_y(index)
        x0, _, x1, _ = self.phone_box
        self.insert_line = self.canvas.create_line(x0 + 8, y, x1 - 8, y, fill=C["accent_hover"], width=4,
                                                   capstyle="round")

    def hide_insert(self):
        if self.insert_line:
            self.canvas.delete(self.insert_line)
            self.insert_line = None

    def contains_root(self, x_root, y_root):
        cx = x_root - self.canvas.winfo_rootx()
        cy = y_root - self.canvas.winfo_rooty()
        return 0 <= cx <= self.canvas.winfo_width() and 0 <= cy <= self.canvas.winfo_height()

    def index_at_root(self, y_root):
        cy = self.canvas.canvasy(y_root - self.canvas.winfo_rooty())
        return self.index_at(cy)

    # ------------------------------------------------------------ eventos

    def _press(self, event):
        cy = self.canvas.canvasy(event.y)
        cid = self.block_at(cy)
        for tag in self.canvas.gettags("current"):
            if tag.startswith("block:"):
                cid = tag[6:]
        self.drag = {"id": cid, "y": event.y, "moving": False}
        self.app.select_component(cid)

    def _motion(self, event):
        if not self.drag or not self.drag["id"]:
            return
        if not self.drag["moving"] and abs(event.y - self.drag["y"]) < 6:
            return
        self.drag["moving"] = True
        self.canvas.configure(cursor="fleur")
        cy = self.canvas.canvasy(event.y)
        self.show_insert(self.index_at(cy))
        # Rolagem automatica perto das bordas
        if event.y < 30:
            self.canvas.yview_scroll(-1, "units")
        elif event.y > self.canvas.winfo_height() - 30:
            self.canvas.yview_scroll(1, "units")

    def _release(self, event):
        self.canvas.configure(cursor="")
        if self.drag and self.drag["moving"] and self.drag["id"]:
            cy = self.canvas.canvasy(event.y)
            self.app.move_component(self.drag["id"], self.index_at(cy))
        self.hide_insert()
        self.drag = None

    def _double(self, event):
        cid = self.block_at(self.canvas.canvasy(event.y))
        if cid:
            self.app.focus_properties()

    def _context(self, event):
        cid = self.block_at(self.canvas.canvasy(event.y))
        if not cid:
            return
        self.app.select_component(cid)
        menu = tk.Menu(self, tearoff=0)
        menu.add_command(label="Duplicar", command=self.app.duplicate_selected)
        menu.add_command(label="Mover para cima", command=lambda: self.app.shift_selected(-1))
        menu.add_command(label="Mover para baixo", command=lambda: self.app.shift_selected(1))
        menu.add_separator()
        menu.add_command(label="Copiar", command=self.app.copy_selected)
        menu.add_command(label="Colar depois", command=self.app.paste_block)
        menu.add_separator()
        menu.add_command(label="Excluir", command=self.app.delete_selected)
        try:
            menu.tk_popup(event.x_root, event.y_root)
        finally:
            menu.grab_release()
