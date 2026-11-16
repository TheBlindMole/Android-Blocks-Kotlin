"""Ferramentas do editor: mapa de navegacao e biblioteca de telas prontas."""

import tkinter as tk
from collections import deque
from tkinter import ttk

from ..catalog import screen_presets
from ..core.model import new_id
from ..core.naming import unique_name
from ..core.resolver import navigation_edges, reachable_screens
from .theme import C, FONT, Dialog
from .text import t

ACTION_NAMES = {"navigate": "abre", "login": "login", "register": "cadastro", "logout": "sair",
                "submit": "salvar", "checkout": "finalizar", "finish_onboarding": "começar"}


class NavigationMap(Dialog):
    """Desenha as telas como caixas e as acoes de navegacao como setas."""

    BOX_W, BOX_H = 150, 46
    COL_GAP, ROW_GAP = 70, 22

    def __init__(self, master, app):
        super().__init__(master, "Mapa de navegação", 980, 640)
        self.app = app
        project = app.project
        top = ttk.Frame(self)
        top.pack(fill="x", padx=12, pady=(12, 4))
        ttk.Label(top, text="Mapa de navegação", style="Title.TLabel").pack(side="left")
        ttk.Button(top, text="Fechar", command=self.close).pack(side="right")
        legend = ("Colunas = distância a partir da tela inicial.  Borda azul: tela inicial.  "
                  "Borda laranja: tela que nenhum caminho alcança.  Clique em uma tela para editá-la.")
        tk.Label(self, text=legend, bg=C["panel"], fg=C["muted"], font=FONT["small"], anchor="w",
                 justify="left").pack(fill="x", padx=12)
        frame = tk.Frame(self, bg=C["bg"])
        frame.pack(fill="both", expand=True, padx=12, pady=10)
        self.canvas = tk.Canvas(frame, bg=C["bg"], highlightthickness=0)
        xs = ttk.Scrollbar(frame, orient="horizontal", command=self.canvas.xview)
        ys = ttk.Scrollbar(frame, orient="vertical", command=self.canvas.yview)
        self.canvas.configure(xscrollcommand=xs.set, yscrollcommand=ys.set)
        ys.pack(side="right", fill="y")
        xs.pack(side="bottom", fill="x")
        self.canvas.pack(fill="both", expand=True)
        self.draw(project)

    def layout(self, project):
        """Coluna de cada tela pela distancia (busca em largura) a partir da inicial."""
        edges = navigation_edges(project)
        start = project.get_start_screen()
        level = {}
        queue = deque()
        if start:
            level[start.name] = 0
            queue.append(start.name)
        if project.navigation in ("bottom", "drawer"):
            for screen in project.screens:
                if screen.in_nav and screen.name not in level:
                    level[screen.name] = 1 if start else 0
                    queue.append(screen.name)
        while queue:
            name = queue.popleft()
            for origin, target, _ in edges:
                if origin == name and target not in level:
                    level[target] = level[name] + 1
                    queue.append(target)
        last = max(level.values(), default=-1) + 1
        for screen in project.screens:
            level.setdefault(screen.name, last)
        columns = {}
        for screen in project.screens:
            columns.setdefault(level[screen.name], []).append(screen.name)
        return columns, edges

    def draw(self, project):
        cv = self.canvas
        columns, edges = self.layout(project)
        reachable = reachable_screens(project)
        start = project.get_start_screen()
        pos = {}
        for col in sorted(columns):
            for row, name in enumerate(columns[col]):
                x = 20 + col * (self.BOX_W + self.COL_GAP)
                y = 20 + row * (self.BOX_H + self.ROW_GAP)
                pos[name] = (x, y)
        # Setas primeiro, para ficarem atras das caixas.
        drawn = set()
        for origin, target, key in edges:
            if (origin, target) in drawn or origin not in pos or target not in pos:
                continue
            drawn.add((origin, target))
            ox, oy = pos[origin]
            tx, ty = pos[target]
            if origin == target:
                continue
            if tx > ox:
                x0, y0, x1, y1 = ox + self.BOX_W, oy + self.BOX_H / 2, tx, ty + self.BOX_H / 2
            else:
                x0, y0, x1, y1 = ox, oy + self.BOX_H / 2, tx + self.BOX_W, ty + self.BOX_H / 2
            mid = (x0 + x1) / 2
            bend = 0 if tx != ox else 40
            cv.create_line(x0, y0, mid + bend, y0, mid + bend, y1, x1, y1, smooth=True, arrow="last",
                           fill=C["accent"] if key == "navigate" else C["success"], width=1.5)
            label = ACTION_NAMES.get(key, key)
            cv.create_text(mid + bend, (y0 + y1) / 2 - 7, text=label, fill=C["muted"], font=FONT["small"])
        screens = {s.name: s for s in project.screens}
        for name, (x, y) in pos.items():
            screen = screens[name]
            outline = C["accent"] if screen is start else (C["warning"] if name not in reachable else C["border"])
            tag = f"screen:{screen.id}"
            cv.create_rectangle(x, y, x + self.BOX_W, y + self.BOX_H, fill=C["card"], outline=outline,
                                width=2, tags=(tag,))
            cv.create_text(x + 10, y + 15, anchor="w", text=t(screen.title or screen.name)[:22], fill=C["text"],
                           font=FONT["bold"], tags=(tag,))
            info = f"{len(screen.components)} blocos" + ("  |  menu" if screen.in_nav else "")
            cv.create_text(x + 10, y + 33, anchor="w", text=info, fill=C["muted"], font=FONT["small"], tags=(tag,))
            cv.tag_bind(tag, "<Button-1>", lambda e, sid=screen.id: self.open_screen(sid))
            cv.tag_bind(tag, "<Enter>", lambda e: cv.configure(cursor="hand2"))
            cv.tag_bind(tag, "<Leave>", lambda e: cv.configure(cursor=""))
        bbox = cv.bbox("all") or (0, 0, 100, 100)
        cv.configure(scrollregion=(0, 0, bbox[2] + 40, bbox[3] + 40))
        if not project.screens:
            cv.create_text(200, 60, text="O projeto ainda não tem telas.", fill=C["muted"], font=FONT["h2"])

    def open_screen(self, sid):
        self.close()
        self.app.select_screen(sid)


class ScreenLibrary(Dialog):
    """Lista de telas prontas que podem ser inseridas no projeto atual."""

    def __init__(self, master, app):
        super().__init__(master, "Telas prontas", 760, 520)
        self.app = app
        root = ttk.Frame(self)
        root.pack(fill="both", expand=True, padx=14, pady=14)
        ttk.Label(root, text="Biblioteca de telas prontas", style="Title.TLabel").pack(anchor="w")
        ttk.Label(root, text="Escolha uma ou mais e clique em Inserir. Depois use Organizar para criar "
                             "as telas que os botões referenciam.", style="Muted.TLabel").pack(anchor="w", pady=(0, 8))
        bar = ttk.Frame(root)
        bar.pack(side="bottom", fill="x", pady=(10, 0))
        ttk.Button(bar, text="Inserir", style="Accent.TButton", command=self.insert).pack(side="right")
        ttk.Button(bar, text="Cancelar", command=self.close).pack(side="right", padx=4)
        self.tree = ttk.Treeview(root, columns=("desc",), show="tree headings", selectmode="extended")
        self.tree.heading("#0", text="Tela")
        self.tree.heading("desc", text="O que contém")
        self.tree.column("#0", width=210, stretch=False)
        self.tree.column("desc", width=480)
        for index, (name, desc, _) in enumerate(screen_presets.PRESETS):
            self.tree.insert("", "end", iid=str(index), text=name, values=(desc,))
        self.tree.pack(fill="both", expand=True)
        self.tree.bind("<Double-1>", lambda e: self.insert())

    def insert(self):
        chosen = [int(i) for i in self.tree.selection()]
        if not chosen:
            return
        app = self.app
        app.before_change()
        used = {s.name for s in app.project.screens}
        inserted = []
        for index in chosen:
            for screen in screen_presets.PRESETS[index][2]():
                screen.id = new_id("s")
                for comp in screen.components:
                    comp.id = new_id()
                screen.name = unique_name(screen.name, used)
                app.project.screens.append(screen)
                inserted.append(screen)
        if not app.project.start_screen and inserted:
            app.project.start_screen = inserted[0].name
        app.current_screen_id = inserted[0].id
        app.selected_id = None
        app.changed(rebuild_props=True, screens=True)
        app.log("Telas inseridas: " + ", ".join(s.name for s in inserted))
        self.close()
