"""Tela inicial e assistente de criacao de projeto."""

import tkinter as tk
from pathlib import Path
from tkinter import ttk, messagebox, colorchooser

from ..catalog import templates as template_catalog
from ..catalog.components import default_props
from ..core.model import Project, Screen, Component, Entity, default_package, new_id
from ..core.naming import is_valid_package
from ..catalog import api_presets
from .. import APP_NAME, __version__
from .theme import C, FONT
from .dialogs import PALETTES, SDK_LEVELS

QUICK_FEATURES = [
    ("splash_screen", "Tela de abertura (splash)"),
    ("local_auth", "Login e cadastro local"),
    ("notifications", "Notificações"),
    ("dark_mode_toggle", "Alternar tema claro/escuro"),
    ("crash_logger", "Registro de falhas"),
    ("connectivity", "Monitor de conexão"),
    ("http_logging", "Log de requisições HTTP"),
    ("ui_tests", "Testes de interface"),
]


class WelcomeFrame(tk.Frame):
    """Primeira tela: criar projeto (assistente) ou abrir um existente."""

    def __init__(self, master, app):
        super().__init__(master, bg=C["bg"])
        self.app = app
        left = tk.Frame(self, bg=C["bg"])
        left.pack(side="left", fill="both", expand=True, padx=(40, 20), pady=30)
        right = tk.Frame(self, bg=C["panel"], width=340)
        right.pack(side="right", fill="y")
        right.pack_propagate(False)

        logo = tk.Canvas(left, width=64, height=64, bg=C["bg"], highlightthickness=0)
        logo.create_rectangle(4, 4, 60, 60, fill=C["accent"], outline="")
        for x0, y0, x1, y1 in ((16, 40, 48, 50), (20, 28, 44, 37), (24, 16, 40, 25)):
            logo.create_rectangle(x0, y0, x1, y1, fill="#FFFFFF", outline="")
        logo.pack(anchor="w")
        tk.Label(left, text=APP_NAME, bg=C["bg"], fg=C["text"], font=FONT["big"]).pack(anchor="w", pady=(10, 0))
        tk.Label(left, text="Crie aplicativos Android completos em Kotlin montando blocos. Tudo offline.",
                 bg=C["bg"], fg=C["muted"], font=FONT["h2"]).pack(anchor="w", pady=(2, 18))
        self.wizard = NewProjectWizard(left, app)
        self.wizard.pack(fill="both", expand=True)

        tk.Label(right, text="Abrir projeto", bg=C["panel"], fg=C["text"], font=FONT["h2"]).pack(anchor="w", padx=18, pady=(30, 6))
        ttk.Button(right, text="Abrir arquivo .dbp...", command=app.open_project).pack(fill="x", padx=18)
        ttk.Button(right, text="Galeria de modelos...", command=app.open_template_gallery).pack(fill="x", padx=18, pady=6)
        tk.Label(right, text="Recentes", bg=C["panel"], fg=C["muted"], font=FONT["small"]).pack(anchor="w", padx=18, pady=(16, 4))
        recent = app.settings.recent()
        if not recent:
            tk.Label(right, text="Nenhum projeto recente.", bg=C["panel"], fg=C["dim"]).pack(anchor="w", padx=18)
        for path in recent:
            item = tk.Frame(right, bg=C["card"], cursor="hand2")
            item.pack(fill="x", padx=18, pady=2)
            name = tk.Label(item, text=Path(path).stem, bg=C["card"], fg=C["text"], font=FONT["bold"], anchor="w")
            name.pack(fill="x", padx=8, pady=(6, 0))
            where = tk.Label(item, text=str(Path(path).parent)[-44:], bg=C["card"], fg=C["dim"], font=FONT["small"], anchor="w")
            where.pack(fill="x", padx=8, pady=(0, 6))
            for w in (item, name, where):
                w.bind("<Button-1>", lambda e, p=path: app.open_project(p))
        tk.Label(right, text=f"Versão {__version__}", bg=C["panel"], fg=C["dim"], font=FONT["small"]).pack(side="bottom", pady=10)


class NewProjectWizard(tk.Frame):
    """Assistente em etapas: identidade, interface, aparencia, ponto de partida e recursos."""

    STEPS = ["Projeto", "Interface", "Aparência", "Ponto de partida", "Recursos", "Resumo"]

    def __init__(self, master, app):
        super().__init__(master, bg=C["bg"])
        self.app = app
        self.step = 0
        self.template = None
        self.v = {
            "name": tk.StringVar(value="MeuApp"), "company": tk.StringVar(value="exemplo"),
            "package": tk.StringVar(value="com.exemplo.meuapp"), "description": tk.StringVar(value=""),
            "ui_mode": tk.StringVar(value="compose"), "navigation": tk.StringVar(value="bottom"),
            "min_sdk": tk.StringVar(value="24 - Android 7.0"), "target_sdk": tk.StringVar(value="35 - Android 15"),
            "theme_mode": tk.StringVar(value="system"), "palette": tk.IntVar(value=0),
            "primary": tk.StringVar(value=PALETTES[0][1]), "secondary": tk.StringVar(value=PALETTES[0][2]),
            "tertiary": tk.StringVar(value=PALETTES[0][3]), "start": tk.StringVar(value="blank"),
            "lang_en": tk.BooleanVar(value=True), "lang_es": tk.BooleanVar(value=False),
            "db": tk.BooleanVar(value=False), "api": tk.BooleanVar(value=False),
        }
        self.features = {key: tk.BooleanVar(value=key in ("splash_screen",)) for key, _ in QUICK_FEATURES}
        self.package_edited = False
        self.v["name"].trace_add("write", lambda *a: self.suggest_package())
        self.v["company"].trace_add("write", lambda *a: self.suggest_package())
        self.steps_bar = tk.Frame(self, bg=C["bg"])
        self.steps_bar.pack(fill="x")
        self.card = tk.Frame(self, bg=C["panel"], highlightthickness=1, highlightbackground=C["border"])
        self.card.pack(fill="both", expand=True, pady=10)
        nav = tk.Frame(self, bg=C["bg"])
        nav.pack(fill="x")
        self.back_btn = ttk.Button(nav, text="Voltar", command=self.back)
        self.back_btn.pack(side="left")
        self.next_btn = ttk.Button(nav, text="Próximo", style="Accent.TButton", command=self.next)
        self.next_btn.pack(side="right")
        ttk.Button(nav, text="Criar já com padrões", command=self.create).pack(side="right", padx=8)
        self.render()

    def suggest_package(self):
        if not self.package_edited:
            self.v["package"].set(default_package(self.v["name"].get(), self.v["company"].get() or "exemplo"))

    def render(self):
        for child in self.steps_bar.winfo_children():
            child.destroy()
        for i, name in enumerate(self.STEPS):
            active = i == self.step
            done = i < self.step
            color = C["accent"] if active else (C["accent_dark"] if done else C["card"])
            cell = tk.Frame(self.steps_bar, bg=color)
            cell.pack(side="left", padx=(0, 4))
            tk.Label(cell, text=f"{i + 1}. {name}", bg=color, fg="#FFFFFF" if active or done else C["muted"],
                     font=FONT["small"], padx=10, pady=5).pack()
        for child in self.card.winfo_children():
            child.destroy()
        getattr(self, f"_step{self.step}")(self.card)
        self.back_btn.state(["!disabled"] if self.step > 0 else ["disabled"])
        self.next_btn.configure(text="Criar projeto" if self.step == len(self.STEPS) - 1 else "Próximo")

    def _title(self, parent, title, subtitle):
        tk.Label(parent, text=title, bg=C["panel"], fg=C["text"], font=FONT["title"]).pack(anchor="w", padx=20, pady=(16, 0))
        tk.Label(parent, text=subtitle, bg=C["panel"], fg=C["muted"]).pack(anchor="w", padx=20, pady=(0, 10))

    def _field(self, parent, label, var, hint=None):
        tk.Label(parent, text=label, bg=C["panel"], fg=C["muted"], font=FONT["small"]).pack(anchor="w", padx=20)
        entry = ttk.Entry(parent, textvariable=var)
        entry.pack(fill="x", padx=20, pady=(0, 2))
        if hint:
            tk.Label(parent, text=hint, bg=C["panel"], fg=C["dim"], font=FONT["small"]).pack(anchor="w", padx=20, pady=(0, 6))
        return entry

    def _step0(self, parent):
        self._title(parent, "Identificação do aplicativo", "Nome, empresa e pacote usados no Android Studio e na Play Store.")
        self._field(parent, "Nome do aplicativo", self.v["name"])
        self._field(parent, "Empresa ou domínio", self.v["company"], "Usado para sugerir o pacote. Ex.: minhaempresa")
        entry = self._field(parent, "Pacote (applicationId)", self.v["package"], "Formato com.empresa.app, sem acentos ou espaços.")
        entry.bind("<Key>", lambda e: setattr(self, "package_edited", True))
        self._field(parent, "Descrição (opcional)", self.v["description"])

    def _radio_cards(self, parent, var, options):
        box = tk.Frame(parent, bg=C["panel"])
        box.pack(fill="x", padx=20, pady=4)
        for value, title, text in options:
            card = tk.Frame(box, bg=C["card"], highlightthickness=2,
                            highlightbackground=C["accent"] if var.get() == value else C["card"], cursor="hand2")
            card.pack(side="left", fill="both", expand=True, padx=(0, 8))
            tk.Label(card, text=title, bg=C["card"], fg=C["text"], font=FONT["bold"]).pack(anchor="w", padx=10, pady=(8, 0))
            tk.Label(card, text=text, bg=C["card"], fg=C["muted"], font=FONT["small"], wraplength=220,
                     justify="left").pack(anchor="w", padx=10, pady=(2, 8))
            for w in [card] + card.winfo_children():
                w.bind("<Button-1>", lambda e, v=value: (var.set(v), self.render()))

    def _step1(self, parent):
        self._title(parent, "Interface e navegação", "Escolha a tecnologia de telas e como o usuário navega pelo app.")
        tk.Label(parent, text="Tecnologia de interface", bg=C["panel"], fg=C["muted"], font=FONT["small"]).pack(anchor="w", padx=20)
        self._radio_cards(parent, self.v["ui_mode"], [
            ("compose", "Jetpack Compose (recomendado)", "Interface declarativa moderna em Kotlin, Material 3."),
            ("views", "XML Views", "Layouts XML clássicos com ViewBinding, Activities e RecyclerView."),
        ])
        tk.Label(parent, text="Navegação principal", bg=C["panel"], fg=C["muted"], font=FONT["small"]).pack(anchor="w", padx=20, pady=(10, 0))
        self._radio_cards(parent, self.v["navigation"], [
            ("bottom", "Barra inferior", "Até 5 telas principais na parte de baixo."),
            ("drawer", "Menu lateral", "Menu que desliza da esquerda."),
            ("stack", "Pilha de telas", "Uma tela leva à outra, com botão voltar."),
        ])
        row = tk.Frame(parent, bg=C["panel"])
        row.pack(fill="x", padx=20, pady=10)
        sdks = [f"{api} - {name}" for api, name in SDK_LEVELS]
        for label, key in (("SDK mínimo", "min_sdk"), ("SDK alvo", "target_sdk")):
            col = tk.Frame(row, bg=C["panel"])
            col.pack(side="left", fill="x", expand=True, padx=(0, 10))
            tk.Label(col, text=label, bg=C["panel"], fg=C["muted"], font=FONT["small"]).pack(anchor="w")
            ttk.Combobox(col, textvariable=self.v[key], values=sdks, state="readonly").pack(fill="x")
        tk.Label(parent, text="SDK mínimo 24 cobre mais de 97% dos aparelhos em uso. SDK alvo 35 atende a Play Store atual.",
                 bg=C["panel"], fg=C["dim"], font=FONT["small"]).pack(anchor="w", padx=20)

    def _step2(self, parent):
        self._title(parent, "Aparência", "Paleta de cores e tema do aplicativo gerado.")
        grid = tk.Frame(parent, bg=C["panel"])
        grid.pack(fill="x", padx=20)
        for i, (name, c1, c2, c3) in enumerate(PALETTES):
            selected = self.v["palette"].get() == i
            cell = tk.Frame(grid, bg=C["card"], highlightthickness=2,
                            highlightbackground=C["accent_hover"] if selected else C["card"], cursor="hand2")
            cell.grid(row=i // 5, column=i % 5, padx=4, pady=4, sticky="ew")
            sw = tk.Canvas(cell, width=110, height=26, bg=C["card"], highlightthickness=0)
            sw.create_rectangle(0, 0, 56, 26, fill=c1, outline="")
            sw.create_rectangle(56, 0, 84, 26, fill=c2, outline="")
            sw.create_rectangle(84, 0, 110, 26, fill=c3, outline="")
            sw.pack(padx=6, pady=(6, 2))
            lb = tk.Label(cell, text=name, bg=C["card"], fg=C["text"], font=FONT["small"])
            lb.pack(pady=(0, 6))
            for w in (cell, sw, lb):
                w.bind("<Button-1>", lambda e, idx=i: self.pick_palette(idx))
        for c in range(5):
            grid.columnconfigure(c, weight=1)
        custom = tk.Frame(parent, bg=C["panel"])
        custom.pack(fill="x", padx=20, pady=10)
        tk.Label(custom, text="Ajuste fino:", bg=C["panel"], fg=C["muted"]).pack(side="left")
        for key, label in (("primary", "Principal"), ("secondary", "Secundária"), ("tertiary", "Destaque")):
            value = self.v[key].get()
            tk.Button(custom, text=label, bg=value, fg="#FFFFFF", relief="flat", activebackground=value, width=11,
                      command=lambda k=key: self.pick_color(k)).pack(side="left", padx=4)
        tk.Label(parent, text="Tema", bg=C["panel"], fg=C["muted"], font=FONT["small"]).pack(anchor="w", padx=20, pady=(8, 0))
        self._radio_cards(parent, self.v["theme_mode"], [
            ("system", "Seguir o sistema", "Claro ou escuro conforme o aparelho."),
            ("light", "Sempre claro", "Fundo claro."), ("dark", "Sempre escuro", "Fundo escuro."),
        ])
        langs = tk.Frame(parent, bg=C["panel"])
        langs.pack(fill="x", padx=20, pady=8)
        tk.Label(langs, text="Idiomas além do português:", bg=C["panel"], fg=C["muted"]).pack(side="left")
        ttk.Checkbutton(langs, text="Inglês", variable=self.v["lang_en"]).pack(side="left", padx=6)
        ttk.Checkbutton(langs, text="Espanhol", variable=self.v["lang_es"]).pack(side="left")

    def pick_palette(self, index):
        self.v["palette"].set(index)
        _, c1, c2, c3 = PALETTES[index]
        self.v["primary"].set(c1)
        self.v["secondary"].set(c2)
        self.v["tertiary"].set(c3)
        self.render()

    def pick_color(self, key):
        color = colorchooser.askcolor(self.v[key].get(), title="Escolher cor")[1]
        if color:
            self.v[key].set(color.upper())
            self.render()

    def _step3(self, parent):
        self._title(parent, "Ponto de partida", f"Comece do zero ou a partir de um dos {len(template_catalog.TEMPLATES)} modelos.")
        self._radio_cards(parent, self.v["start"], [
            ("blank", "Projeto em branco", "Uma tela inicial com título e lista de exemplo."),
            ("template", "Usar um modelo", "Delivery, loja, clima, finanças, saúde, educação e muito mais."),
        ])
        if self.v["start"].get() != "template":
            return
        frame = tk.Frame(parent, bg=C["panel"])
        frame.pack(fill="both", expand=True, padx=20, pady=8)
        search = tk.StringVar()
        ttk.Entry(frame, textvariable=search).pack(fill="x")
        tree = ttk.Treeview(frame, columns=("n", "c"), show="headings", height=9, selectmode="browse")
        tree.heading("n", text="Modelo")
        tree.heading("c", text="Categoria")
        tree.column("n", width=280)
        tree.column("c", width=200)
        tree.pack(fill="both", expand=True, pady=4)
        desc = tk.Label(frame, text="", bg=C["panel"], fg=C["muted"], wraplength=640, justify="left", anchor="w")
        desc.pack(fill="x")

        def fill(*_):
            tree.delete(*tree.get_children())
            q = search.get().lower()
            for i, tpl in enumerate(template_catalog.TEMPLATES):
                if q and q not in tpl["name"].lower() and q not in tpl["category"].lower():
                    continue
                tree.insert("", "end", iid=str(i), values=(tpl["name"], tpl["category"]))
            if self.template is not None:
                idx = str(template_catalog.TEMPLATES.index(self.template))
                if tree.exists(idx):
                    tree.selection_set(idx)
                    tree.see(idx)

        def select(_=None):
            sel = tree.selection()
            if sel:
                self.template = template_catalog.TEMPLATES[int(sel[0])]
                desc.configure(text=f"{self.template['description']}  ({len(self.template['screens'])} telas)")
                if self.v["name"].get() in ("", "MeuApp"):
                    pass
        search.trace_add("write", fill)
        tree.bind("<<TreeviewSelect>>", select)
        fill()

    def _step4(self, parent):
        self._title(parent, "Recursos iniciais", "Marque o que deseja incluir agora. Tudo pode ser alterado depois.")
        grid = tk.Frame(parent, bg=C["panel"])
        grid.pack(fill="x", padx=20)
        for i, (key, label) in enumerate(QUICK_FEATURES):
            ttk.Checkbutton(grid, text=label, variable=self.features[key]).grid(row=i // 2, column=i % 2, sticky="w", pady=3, padx=(0, 30))
        tk.Label(parent, text="Dados", bg=C["panel"], fg=C["muted"], font=FONT["small"]).pack(anchor="w", padx=20, pady=(12, 0))
        ttk.Checkbutton(parent, text="Banco de dados local (cria a entidade Item com telas de lista e cadastro)",
                        variable=self.v["db"]).pack(anchor="w", padx=20)
        ttk.Checkbutton(parent, text="API REST de exemplo (JSONPlaceholder, posts)", variable=self.v["api"]).pack(anchor="w", padx=20)

    def _step5(self, parent):
        self._title(parent, "Resumo", "Confira e clique em Criar projeto.")
        v = self.v
        start = self.template["name"] if v["start"].get() == "template" and self.template else "Projeto em branco"
        feats = [label for key, label in QUICK_FEATURES if self.features[key].get()]
        lines = [
            ("Nome", v["name"].get()), ("Pacote", v["package"].get()),
            ("Interface", "Jetpack Compose" if v["ui_mode"].get() == "compose" else "XML Views"),
            ("Navegação", {"bottom": "Barra inferior", "drawer": "Menu lateral", "stack": "Pilha"}[v["navigation"].get()]),
            ("SDK", f"mínimo {v['min_sdk'].get()} / alvo {v['target_sdk'].get()}"),
            ("Cores", f"{v['primary'].get()}  {v['secondary'].get()}  {v['tertiary'].get()}"),
            ("Ponto de partida", start), ("Recursos", ", ".join(feats) or "nenhum"),
            ("Banco / API", f"{'sim' if v['db'].get() else 'não'} / {'sim' if v['api'].get() else 'não'}"),
        ]
        for label, value in lines:
            row = tk.Frame(parent, bg=C["panel"])
            row.pack(fill="x", padx=20, pady=2)
            tk.Label(row, text=label, bg=C["panel"], fg=C["muted"], width=18, anchor="w").pack(side="left")
            tk.Label(row, text=value, bg=C["panel"], fg=C["text"], anchor="w", wraplength=520, justify="left").pack(side="left")

    def back(self):
        if self.step > 0:
            self.step -= 1
            self.render()

    def next(self):
        if self.step == 0 and not is_valid_package(self.v["package"].get().strip()):
            messagebox.showerror("Pacote inválido", "Use o formato com.empresa.app (minúsculas, sem acentos).")
            return
        if self.step == 3 and self.v["start"].get() == "template" and self.template is None:
            messagebox.showinfo("Escolha um modelo", "Selecione um modelo na lista ou escolha Projeto em branco.")
            return
        if self.step < len(self.STEPS) - 1:
            self.step += 1
            self.render()
        else:
            self.create()

    def build(self):
        v = self.v
        package = v["package"].get().strip()
        if not is_valid_package(package):
            package = default_package(v["name"].get() or "MeuApp")
        if v["start"].get() == "template" and self.template:
            project = template_catalog.build_project(self.template, v["name"].get() or self.template["name"], package)
            project.navigation = v["navigation"].get() if v["navigation"].get() != "bottom" else project.navigation
        else:
            project = Project(name=v["name"].get() or "MeuApp", package=package)
            project.navigation = v["navigation"].get()
            project.samples = {"default": template_catalog.DEFAULT}
            home = Screen(name="Inicio", title="Início", in_nav=True, icon="home", components=[
                Component("title", dict(default_props("title"), text=f"Bem-vindo ao {project.name}"), new_id()),
                Component("text", dict(default_props("text"), text="Este é o seu novo aplicativo."), new_id()),
                Component("list", dict(default_props("list"), item_action="navigate:Detalhe"), new_id()),
            ])
            detail = Screen(name="Detalhe", title="Detalhes", icon="info", components=[
                Component("item_detail", default_props("item_detail"), new_id()),
                Component("button", dict(default_props("button"), text="Compartilhar", action="share_item"), new_id()),
            ])
            about = Screen(name="Sobre", title="Sobre", in_nav=True, icon="info", components=[
                Component("title", dict(default_props("title"), text=project.name), new_id()),
                Component("text", dict(default_props("text"), text=v["description"].get() or "Aplicativo criado com o DroidBlocks."), new_id()),
            ])
            project.screens = [home, detail, about]
            project.start_screen = "Inicio"
        project.description = v["description"].get() or project.description
        project.ui_mode = v["ui_mode"].get()
        project.min_sdk = int(v["min_sdk"].get().split(" ")[0])
        project.target_sdk = project.compile_sdk = int(v["target_sdk"].get().split(" ")[0])
        if project.min_sdk > project.target_sdk:
            project.min_sdk = 24
        project.theme_mode = v["theme_mode"].get()
        if v["start"].get() != "template" or v["palette"].get() != 0:
            project.primary_color = v["primary"].get()
            project.secondary_color = v["secondary"].get()
            project.tertiary_color = v["tertiary"].get()
        project.languages = ["pt"] + (["en"] if v["lang_en"].get() else []) + (["es"] if v["lang_es"].get() else [])
        for key, var in self.features.items():
            if var.get() and key not in project.features:
                project.features.append(key)
        if self.features["local_auth"].get() and not project.screen_by_name("Login"):
            login, register = template_catalog.login_screens(project.get_start_screen().name)
            project.screens = [login, register] + project.screens
            project.start_screen = "Login"
        if v["db"].get() and not project.entity_by_name("Item"):
            from .dialogs import crud_screens
            entity = Entity("Item", [["name", "String"], ["description", "String"], ["price", "Double"]])
            project.entities.append(entity)
            project.screens += crud_screens(entity)
        if v["api"].get() and not project.api_by_name("JsonPlaceholder"):
            project.apis.append(api_presets.jsonplaceholder(("posts",)))
            from ..catalog.templates import list_screen
            project.screens.append(list_screen("Posts", "Posts", "api:JsonPlaceholder.getPosts", detail="Detalhe" if project.screen_by_name("Detalhe") else None, icon="list"))
        return project

    def create(self):
        self.app.load_project(self.build(), None)
