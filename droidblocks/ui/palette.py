"""Painel esquerdo: paleta de blocos, funcionalidades e algoritmos."""

import tkinter as tk
from tkinter import ttk

from ..catalog import components as comp_catalog
from ..catalog import features as feature_catalog
from ..catalog import algorithms as algo_catalog
from ..catalog.libraries import LIBRARIES
from .theme import C, FONT, BLOCK_COLORS, ScrollFrame, Tooltip, text_widget
from .text import t


class DragManager:
    """Arrastar blocos da paleta para o celular, entre janelas do Tk."""

    def __init__(self, app):
        self.app = app
        self.ghost = None
        self.ctype = None

    def start(self, ctype, event):
        self.ctype = ctype
        self.start_xy = (event.x_root, event.y_root)
        self.active = False

    def motion(self, event):
        if not self.ctype:
            return
        if not self.active:
            if abs(event.x_root - self.start_xy[0]) + abs(event.y_root - self.start_xy[1]) < 8:
                return
            self.active = True
            spec = comp_catalog.COMPONENTS[self.ctype]
            self.ghost = tk.Toplevel(self.app.root)
            self.ghost.wm_overrideredirect(True)
            try:
                self.ghost.attributes("-alpha", 0.88)
            except tk.TclError:
                pass
            color = BLOCK_COLORS.get(spec.category, C["accent"])
            tk.Label(self.ghost, text=f"  {spec.glyph}   {t(spec.label)}  ", bg=color, fg="#FFFFFF",
                     font=FONT["block"], padx=10, pady=8).pack()
        self.ghost.geometry(f"+{event.x_root + 12}+{event.y_root + 8}")
        canvas = self.app.editor.canvas
        if canvas.contains_root(event.x_root, event.y_root):
            canvas.show_insert(canvas.index_at_root(event.y_root))
        else:
            canvas.hide_insert()

    def drop(self, event):
        canvas = self.app.editor.canvas
        if self.active and canvas.contains_root(event.x_root, event.y_root):
            self.app.add_component(self.ctype, canvas.index_at_root(event.y_root))
        canvas.hide_insert()
        if self.ghost:
            self.ghost.destroy()
        self.ghost = None
        self.ctype = None
        self.active = False


class BlockPalette(ttk.Frame):
    """Lista de blocos por categoria. Arraste para o celular ou de duplo clique."""

    def __init__(self, master, app):
        super().__init__(master)
        self.app = app
        self.drag = DragManager(app)
        top = ttk.Frame(self)
        top.pack(fill="x", padx=8, pady=(8, 4))
        self.search = tk.StringVar()
        entry = ttk.Entry(top, textvariable=self.search)
        entry.pack(fill="x")
        self._placeholder(entry, "Buscar bloco...")
        self.search.trace_add("write", lambda *a: self.build())
        ttk.Label(self, text="Arraste para a tela ou de duplo clique", style="Muted.TLabel",
                  font=FONT["small"]).pack(anchor="w", padx=10)
        self.scroll = ScrollFrame(self)
        self.scroll.pack(fill="both", expand=True, pady=(4, 0))
        self.build()

    def _placeholder(self, entry, text):
        def on_focus_in(_):
            if self.search.get() == text:
                self.search.set("")
        def on_focus_out(_):
            if not self.search.get():
                self.search.set(text)
        self.search.set(text)
        self._ph = text
        entry.bind("<FocusIn>", on_focus_in)
        entry.bind("<FocusOut>", on_focus_out)

    def build(self):
        body = self.scroll.body
        for child in body.winfo_children():
            child.destroy()
        query = self.search.get().strip().lower()
        if query == getattr(self, "_ph", "").lower():
            query = ""
        for category, items in comp_catalog.by_category().items():
            matches = [c for c in items if not query or query in t(c.label).lower() or query in c.description.lower()]
            if not matches:
                continue
            tk.Label(body, text=t(category).upper(), bg=C["panel"], fg=C["muted"], font=FONT["small"],
                     anchor="w").pack(fill="x", padx=10, pady=(10, 3))
            for spec in matches:
                self._item(body, spec)
        self.scroll.bind_children()

    def _item(self, parent, spec):
        color = BLOCK_COLORS.get(spec.category, C["accent"])
        row = tk.Frame(parent, bg=C["card"], cursor="hand2")
        row.pack(fill="x", padx=8, pady=2)
        bar = tk.Frame(row, bg=color, width=6)
        bar.pack(side="left", fill="y")
        glyph = tk.Label(row, text=spec.glyph, bg=C["card"], fg=color, font=FONT["block_small"], width=6)
        glyph.pack(side="left", padx=(4, 0), pady=6)
        label = tk.Label(row, text=t(spec.label), bg=C["card"], fg=C["text"], font=FONT["base"], anchor="w")
        label.pack(side="left", fill="x", expand=True, pady=6)
        Tooltip(row, t(spec.description))
        for widget in (row, bar, glyph, label):
            widget.bind("<ButtonPress-1>", lambda e, s=spec.type: self.drag.start(s, e))
            widget.bind("<B1-Motion>", self.drag.motion)
            widget.bind("<ButtonRelease-1>", self.drag.drop)
            widget.bind("<Double-Button-1>", lambda e, s=spec.type: self.app.add_component(s))
            widget.bind("<Enter>", lambda e, r=row, g=glyph, l=label: [w.configure(bg=C["card_hover"]) for w in (r, g, l)])
            widget.bind("<Leave>", lambda e, r=row, g=glyph, l=label: [w.configure(bg=C["card"]) for w in (r, g, l)])


class CatalogBrowser(ttk.Frame):
    """Arvore com itens marcaveis (funcionalidades ou algoritmos) e painel de detalhes."""

    def __init__(self, master, app, kind):
        super().__init__(master)
        self.app = app
        self.kind = kind
        top = ttk.Frame(self)
        top.pack(fill="x", padx=8, pady=(8, 4))
        self.search = tk.StringVar()
        ttk.Entry(top, textvariable=self.search).pack(side="left", fill="x", expand=True)
        self.search.trace_add("write", lambda *a: self.refresh())
        self.only_active = tk.BooleanVar(value=False)
        ttk.Checkbutton(top, text="Ativas", variable=self.only_active, command=self.refresh).pack(side="left", padx=(6, 0))
        hint = ("Duplo clique ou Espaco para ativar. [a] = adicionada automaticamente."
                if kind == "features" else "Duplo clique ou Espaco para incluir no projeto.")
        ttk.Label(self, text=t(hint), style="Muted.TLabel", font=FONT["small"], wraplength=260).pack(anchor="w", padx=10)
        pane = ttk.PanedWindow(self, orient="vertical")
        pane.pack(fill="both", expand=True, pady=4)
        tree_frame = ttk.Frame(pane)
        self.tree = ttk.Treeview(tree_frame, show="tree", selectmode="browse")
        scroll = ttk.Scrollbar(tree_frame, orient="vertical", command=self.tree.yview)
        self.tree.configure(yscrollcommand=scroll.set)
        self.tree.pack(side="left", fill="both", expand=True)
        scroll.pack(side="right", fill="y")
        self.tree.tag_configure("on", foreground=C["accent_hover"])
        self.tree.tag_configure("auto", foreground=C["success"])
        self.tree.tag_configure("cat", foreground=C["muted"], font=FONT["small"])
        pane.add(tree_frame, weight=3)
        self.details = text_widget(pane, height=8)
        self.details.configure(state="disabled", bg=C["panel"])
        pane.add(self.details, weight=1)
        self.tree.bind("<<TreeviewSelect>>", lambda e: self.show_details())
        self.tree.bind("<Double-Button-1>", lambda e: self.toggle())
        self.tree.bind("<space>", lambda e: self.toggle())
        self.open_categories = set()
        self.refresh()

    def items(self):
        if self.kind == "features":
            return [(cat, [(f.key, t(f.name), t(f.description)) for f in items])
                    for cat, items in feature_catalog.by_category().items()]
        return [(cat, [(a.key, t(a.name), t(a.description)) for a in items])
                for cat, items in algo_catalog.by_category().items()]

    def state_of(self, key):
        project = self.app.project
        if self.kind == "features":
            if key in project.features:
                return "on"
            if key in self.app.resolved_keys():
                return "auto"
            return "off"
        return "on" if key in project.algorithms else "off"

    def refresh(self):
        for item in self.tree.get_children():
            if self.tree.item(item, "open"):
                self.open_categories.add(item)
        selected = self.tree.selection()
        self.tree.delete(*self.tree.get_children())
        query = self.search.get().strip().lower()
        for category, entries in self.items():
            rows = []
            for key, name, desc in entries:
                if query and query not in name.lower() and query not in desc.lower():
                    continue
                state = self.state_of(key)
                if self.only_active.get() and state == "off":
                    continue
                rows.append((key, name, state))
            if not rows:
                continue
            active = sum(1 for r in rows if r[2] != "off")
            cat_id = "cat:" + category
            self.tree.insert("", "end", iid=cat_id, text=f"{t(category)}  ({active}/{len(rows)})", tags=("cat",),
                             open=bool(query) or cat_id in self.open_categories or self.only_active.get())
            for key, name, state in rows:
                mark = {"on": "[x]", "auto": "[a]", "off": "[  ]"}[state]
                self.tree.insert(cat_id, "end", iid=key, text=f"{mark}  {name}", tags=(state,))
        if selected and self.tree.exists(selected[0]):
            self.tree.selection_set(selected[0])
            self.tree.see(selected[0])

    def toggle(self):
        selection = self.tree.selection()
        if not selection or selection[0].startswith("cat:"):
            if selection:
                item = selection[0]
                self.tree.item(item, open=not self.tree.item(item, "open"))
            return "break"
        key = selection[0]
        if self.kind == "features":
            self.app.toggle_feature(key)
        else:
            self.app.toggle_algorithm(key)
        return "break"

    def show_details(self):
        selection = self.tree.selection()
        self.details.configure(state="normal")
        self.details.delete("1.0", "end")
        if selection and not selection[0].startswith("cat:"):
            key = selection[0]
            if self.kind == "features":
                f = feature_catalog.FEATURES[key]
                lines = [t(f.name), "", t(f.description)]
                if f.libs or f.libs_compose or f.libs_views:
                    mods = [LIBRARIES[l].module for l in f.libs + f.libs_compose + f.libs_views if l in LIBRARIES]
                    lines += ["", "Bibliotecas: " + ", ".join(dict.fromkeys(mods))]
                if f.permissions:
                    lines += ["Permissões: " + ", ".join(p.split(".")[-1] for p in f.permissions)]
                files = list(f.files) + list(f.files_compose) + list(f.files_views)
                if files:
                    lines += ["Arquivos: " + ", ".join(files)]
                if f.requires:
                    lines += ["Depende de: " + ", ".join(t(feature_catalog.FEATURES[r].name) for r in f.requires)]
                if f.notes:
                    lines += ["", "Atenção: " + t(f.notes)]
            else:
                a = algo_catalog.ALGORITHMS[key]
                lines = [t(a.name), "", t(a.description), "", f"Arquivo: algorithms/{a.cls}.kt", "",
                         "Teste incluído: " + a.test.split("\n")[0][:120]]
            self.details.insert("1.0", "\n".join(lines))
        self.details.configure(state="disabled")
