"""Janelas auxiliares: modelos, APIs, banco de dados, configuracoes, codigo e geracao."""

import copy
import os
import subprocess
import sys
import threading
import tkinter as tk
from pathlib import Path
from tkinter import ttk, filedialog, messagebox, colorchooser

from ..catalog import templates as template_catalog
from ..catalog import api_presets
from ..catalog.libraries import DEFAULT_VERSIONS
from ..core.model import Api, ApiModel, ApiField, Endpoint, Entity, Screen, Component, parse_fields, fields_to_text, new_id
from ..core.naming import to_pascal, is_valid_package, to_camel
from ..core import json_infer
from ..core import android_tools
from ..core.generator import generate, write_project, zip_project
from .theme import C, FONT, Dialog, text_widget, ScrollFrame
from .text import t

PALETTES = [
    ("Azul oceano", "#1E88E5", "#0D47A1", "#26C6DA"),
    ("Azul noite", "#1A237E", "#283593", "#5C6BC0"),
    ("Azul elétrico", "#2F81F7", "#1F4FBF", "#00B8D9"),
    ("Índigo", "#3949AB", "#1A237E", "#7986CB"),
    ("Ciano", "#00ACC1", "#006064", "#4DD0E1"),
    ("Verde", "#43A047", "#1B5E20", "#9CCC65"),
    ("Roxo", "#7B1FA2", "#4A148C", "#BA68C8"),
    ("Vermelho", "#E53935", "#B71C1C", "#FF8A65"),
    ("Laranja", "#FB8C00", "#E65100", "#FFD54F"),
    ("Grafite", "#37474F", "#212121", "#78909C"),
]

SDK_LEVELS = [(24, "Android 7.0"), (26, "Android 8.0"), (28, "Android 9"), (29, "Android 10"),
              (30, "Android 11"), (31, "Android 12"), (33, "Android 13"), (34, "Android 14"), (35, "Android 15"),
              (36, "Android 16")]


def open_folder(path):
    """Abre uma pasta no gerenciador de arquivos do sistema."""
    try:
        if sys.platform.startswith("win"):
            os.startfile(str(path))
        elif sys.platform == "darwin":
            subprocess.Popen(["open", str(path)])
        else:
            subprocess.Popen(["xdg-open", str(path)])
    except Exception:
        pass


# ======================================================================= modelos

class TemplateGallery(Dialog):
    """Galeria com os modelos de aplicativos prontos."""

    def __init__(self, master, embedded=False):
        super().__init__(master, "Modelos de aplicativos", 1000, 640)
        self.selected = None
        root = ttk.Frame(self)
        root.pack(fill="both", expand=True, padx=12, pady=12)
        top = ttk.Frame(root)
        top.pack(fill="x")
        ttk.Label(top, text=f"{len(template_catalog.TEMPLATES)} modelos prontos", style="Title.TLabel").pack(side="left")
        self.search = tk.StringVar()
        entry = ttk.Entry(top, textvariable=self.search, width=34)
        entry.pack(side="right")
        ttk.Label(top, text="Buscar:", style="Muted.TLabel").pack(side="right", padx=6)
        self.search.trace_add("write", lambda *a: self.fill())
        self.buttons(root, [("Cancelar", self.close, None), ("Usar este modelo", self.use, "Accent.TButton")]).pack(side="bottom", fill="x")
        body = ttk.PanedWindow(root, orient="horizontal")
        body.pack(fill="both", expand=True, pady=10)
        left = ttk.Frame(body)
        self.cats = tk.Listbox(left, bg=C["panel2"], fg=C["text"], selectbackground=C["accent"], relief="flat",
                               highlightthickness=0, font=FONT["base"], activestyle="none", exportselection=False,
                               width=30)
        self.cats.pack(fill="both", expand=True)
        self.cats.insert("end", "Todas as categorias")
        for cat in template_catalog.categories():
            count = sum(1 for x in template_catalog.TEMPLATES if x["category"] == cat)
            self.cats.insert("end", f"{cat} ({count})")
        self.cats.selection_set(0)
        self.cats.bind("<<ListboxSelect>>", lambda e: self.fill())
        body.add(left, weight=1)
        mid = ttk.Frame(body)
        self.tree = ttk.Treeview(mid, columns=("cat", "screens", "features"), show="headings", selectmode="browse")
        for col, text, width in (("cat", "Modelo", 260), ("screens", "Telas", 60), ("features", "Recursos", 80)):
            self.tree.heading(col, text=text)
            self.tree.column(col, width=width, anchor="w" if col == "cat" else "center")
        scroll = ttk.Scrollbar(mid, orient="vertical", command=self.tree.yview)
        self.tree.configure(yscrollcommand=scroll.set)
        self.tree.pack(side="left", fill="both", expand=True)
        scroll.pack(side="right", fill="y")
        self.tree.bind("<<TreeviewSelect>>", lambda e: self.details())
        self.tree.bind("<Double-Button-1>", lambda e: self.use())
        body.add(mid, weight=2)
        right = ttk.Frame(body)
        self.info = text_widget(right, height=20)
        self.info.pack(fill="both", expand=True)
        self.info.configure(state="disabled", bg=C["panel"])
        body.add(right, weight=2)
        self.fill()

    def fill(self):
        self.tree.delete(*self.tree.get_children())
        sel = self.cats.curselection()
        cats = template_catalog.categories()
        category = cats[sel[0] - 1] if sel and sel[0] > 0 else None
        query = self.search.get().lower().strip()
        for index, tpl in enumerate(template_catalog.TEMPLATES):
            if category and tpl["category"] != category:
                continue
            if query and query not in tpl["name"].lower() and query not in tpl["description"].lower():
                continue
            self.tree.insert("", "end", iid=str(index), values=(tpl["name"], len(tpl["screens"]), len(tpl["features"])))
        children = self.tree.get_children()
        if children:
            self.tree.selection_set(children[0])

    def details(self):
        sel = self.tree.selection()
        if not sel:
            return
        tpl = template_catalog.TEMPLATES[int(sel[0])]
        from ..catalog.features import FEATURES
        lines = [tpl["name"], tpl["category"], "", tpl["description"], "", "Telas:"]
        lines += [f"  - {s.title or s.name} ({len(s.components)} blocos)" for s in tpl["screens"]]
        lines += ["", "Funcionalidades:"] + [f"  - {t(FEATURES[f].name)}" for f in tpl["features"]]
        if tpl["entities"]:
            lines += ["", "Banco de dados:"] + [f"  - {e.name}: " + ", ".join(f[0] for f in e.fields) for e in tpl["entities"]]
        if tpl["apis"]:
            lines += ["", "APIs:"] + [f"  - {a.name} ({a.base_url})" for a in tpl["apis"]]
        lines += ["", f"Navegação: {dict(stack='pilha', bottom='barra inferior', drawer='menu lateral')[tpl['navigation']]}",
                  f"Cor principal: {tpl['color']}"]
        self.info.configure(state="normal")
        self.info.delete("1.0", "end")
        self.info.insert("1.0", "\n".join(lines))
        self.info.configure(state="disabled")

    def use(self):
        sel = self.tree.selection()
        if sel:
            self.result = template_catalog.TEMPLATES[int(sel[0])]
            self.close()


# ======================================================================= APIs

class ApiEditor(Dialog):
    """Cadastro de APIs REST, endpoints, modelos e mapeamento para listas."""

    def __init__(self, master, project):
        super().__init__(master, "APIs REST", 1100, 760)
        self.apis = copy.deepcopy(project.apis)
        self.current = None
        self.current_ep = None
        root = ttk.Frame(self)
        root.pack(fill="both", expand=True, padx=12, pady=12)
        ttk.Label(root, text="APIs do aplicativo", style="Title.TLabel").pack(anchor="w")
        ttk.Label(root, text="Cada API gera um serviço Retrofit, modelos com Gson e o mapeamento para as listas. "
                             "Use 'API pronta' para exemplos públicos sem chave.", style="Muted.TLabel").pack(anchor="w", pady=(0, 8))
        self.buttons(root, [("Cancelar", self.close, None), ("Salvar APIs", self.save, "Accent.TButton")]).pack(side="bottom", fill="x", pady=(8, 0))
        body = ttk.PanedWindow(root, orient="horizontal")
        body.pack(fill="both", expand=True)
        left = ttk.Frame(body)
        self.list = tk.Listbox(left, bg=C["panel2"], fg=C["text"], selectbackground=C["accent"], relief="flat",
                               highlightthickness=0, exportselection=False, font=FONT["base"], width=24)
        bar = ttk.Frame(left)
        bar.pack(side="bottom", fill="x", pady=6)
        self.list.pack(fill="both", expand=True)
        self.list.bind("<<ListboxSelect>>", lambda e: self.select_api())
        preset = ttk.Menubutton(bar, text="Adicionar API pronta")
        menu = tk.Menu(preset, tearoff=0)
        for name in api_presets.PRESETS:
            menu.add_command(label=name, command=lambda n=name: self.add_preset(n))
        preset["menu"] = menu
        preset.pack(side="bottom", fill="x", pady=(4, 0))
        ttk.Button(bar, text="Nova", width=6, command=self.add_api).pack(side="left")
        ttk.Button(bar, text="Remover", width=8, command=self.remove_api).pack(side="right")
        body.add(left, weight=1)
        self.form = ttk.Frame(body)
        body.add(self.form, weight=4)
        self.refresh_list()

    def refresh_list(self, select=None):
        self.list.delete(0, "end")
        for api in self.apis:
            self.list.insert("end", f"{api.name}  ({len(api.endpoints)} endpoints)")
        if self.apis:
            index = select if select is not None else 0
            self.list.selection_set(index)
            self.select_api()
        else:
            self.build_form(None)

    def add_api(self):
        name = f"Api{len(self.apis) + 1}"
        api = Api(name=name, base_url="https://jsonplaceholder.typicode.com/",
                  models=[ApiModel("Post", [ApiField("id", "Long"), ApiField("title", "String"), ApiField("body", "String")])],
                  endpoints=[Endpoint("getPosts", "GET", "posts", "Post", True, mapping={"title": "title", "subtitle": "body", "id": "id"})])
        self.apis.append(api)
        self.refresh_list(len(self.apis) - 1)

    def add_preset(self, name):
        api = api_presets.PRESETS[name]()
        existing = {a.name for a in self.apis}
        if api.name in existing:
            if not messagebox.askyesno("API existente", f"A API {api.name} ja existe. Substituir?", parent=self):
                return
            self.apis = [a for a in self.apis if a.name != api.name]
        self.apis.append(api)
        self.refresh_list(len(self.apis) - 1)

    def remove_api(self):
        if self.current is None:
            return
        self.apis.remove(self.current)
        self.current = None
        self.refresh_list()

    def select_api(self):
        sel = self.list.curselection()
        if sel:
            self.current = self.apis[sel[0]]
            self.build_form(self.current)

    def build_form(self, api):
        for child in self.form.winfo_children():
            child.destroy()
        if api is None:
            ttk.Label(self.form, text="Nenhuma API. Clique em 'Nova' ou 'API pronta'.", style="Muted.TLabel").pack(pady=40)
            return
        grid = ttk.Frame(self.form)
        grid.pack(fill="x", padx=10)
        self.v_name = tk.StringVar(value=api.name)
        self.v_url = tk.StringVar(value=api.base_url)
        self.v_auth = tk.StringVar(value=api.auth)
        self.v_header = tk.StringVar(value=api.api_key_header)
        pairs = [
            ("Nome", ttk.Entry(grid, textvariable=self.v_name, width=18)),
            ("URL base", ttk.Entry(grid, textvariable=self.v_url)),
            ("Autenticação", ttk.Combobox(grid, textvariable=self.v_auth, values=["none", "bearer", "api_key"],
                                          state="readonly", width=16)),
            ("Cabeçalho da chave", ttk.Entry(grid, textvariable=self.v_header)),
        ]
        for i, (label, widget) in enumerate(pairs):
            ttk.Label(grid, text=label, style="Muted.TLabel").grid(row=i // 2, column=(i % 2) * 2, sticky="w", pady=3, padx=(0, 6))
            widget.grid(row=i // 2, column=(i % 2) * 2 + 1, sticky="ew", pady=3, padx=(0, 12))
        grid.columnconfigure(3, weight=1)
        ttk.Label(self.form, text="bearer: envia o token salvo (TokenStore). api_key: lê a chave de local.properties.",
                  style="Muted.TLabel", font=FONT["small"]).pack(anchor="w", padx=10)
        for var in (self.v_name, self.v_url, self.v_auth, self.v_header):
            var.trace_add("write", lambda *a: self.apply_api())
        tabs = ttk.Notebook(self.form)
        tabs.pack(fill="both", expand=True, padx=10, pady=8)
        ep_tab = ttk.Frame(tabs)
        md_tab = ttk.Frame(tabs)
        tabs.add(ep_tab, text="Endpoints")
        tabs.add(md_tab, text="Modelos (JSON)")
        self._endpoints_tab(ep_tab, api)
        self._models_tab(md_tab, api)

    def apply_api(self):
        if self.current is None:
            return
        self.current.name = to_pascal(self.v_name.get(), "Api")
        self.current.base_url = self.v_url.get().strip()
        self.current.auth = self.v_auth.get()
        self.current.api_key_header = self.v_header.get().strip() or "X-API-Key"

    # ----- endpoints
    def _endpoints_tab(self, parent, api):
        top = ttk.Frame(parent)
        top.pack(fill="both", expand=True)
        self.ep_tree = ttk.Treeview(top, columns=("m", "p", "r"), show="headings", height=3, selectmode="browse")
        for col, text, width in (("m", "Método", 70), ("p", "Caminho", 260), ("r", "Resposta", 160)):
            self.ep_tree.heading(col, text=text)
            self.ep_tree.column(col, width=width)
        self.ep_tree.pack(fill="x")
        self.ep_tree.bind("<<TreeviewSelect>>", lambda e: self.select_endpoint())
        bar = ttk.Frame(top)
        bar.pack(fill="x", pady=4)
        ttk.Button(bar, text="Novo endpoint", command=self.add_endpoint).pack(side="left")
        ttk.Button(bar, text="Remover", command=self.remove_endpoint).pack(side="left", padx=4)
        self.ep_form = ttk.Frame(top)
        self.ep_form.pack(fill="both", expand=True)
        self.refresh_endpoints()

    def refresh_endpoints(self, select=0):
        self.ep_tree.delete(*self.ep_tree.get_children())
        for i, ep in enumerate(self.current.endpoints):
            ret = (f"List<{ep.model}>" if ep.returns_list else ep.model) + (f" .{ep.wrapper_field}" if ep.wrapper_field else "")
            self.ep_tree.insert("", "end", iid=str(i), values=(ep.method, f"{ep.name}: /{ep.path}", ret))
        if self.current.endpoints:
            self.ep_tree.selection_set(str(min(select, len(self.current.endpoints) - 1)))
        else:
            for child in self.ep_form.winfo_children():
                child.destroy()

    def add_endpoint(self):
        model = self.current.models[0].name if self.current.models else ""
        self.current.endpoints.append(Endpoint(f"endpoint{len(self.current.endpoints) + 1}", "GET", "", model, True))
        self.refresh_endpoints(len(self.current.endpoints) - 1)

    def remove_endpoint(self):
        sel = self.ep_tree.selection()
        if sel:
            del self.current.endpoints[int(sel[0])]
            self.refresh_endpoints()

    def select_endpoint(self):
        sel = self.ep_tree.selection()
        for child in self.ep_form.winfo_children():
            child.destroy()
        if not sel:
            return
        index = int(sel[0])
        ep = self.current.endpoints[index]
        models = [""] + [m.name for m in self.current.models]
        fields = [
            ("name", "Nome da função", "entry", None), ("method", "Método", "combo", ["GET", "POST", "PUT", "PATCH", "DELETE"]),
            ("path", "Caminho (ex.: products/{id})", "entry", None),
            ("query", "Query fixa (ex.: limit=20&q=x)", "entry", None),
            ("model", "Modelo da resposta", "combo", models), ("returns_list", "Resposta é uma lista JSON", "bool", None),
            ("wrapper_field", "Campo com a lista", "entry", None),
            ("body_model", "Modelo do corpo (POST/PUT)", "combo", models),
        ]
        grid = ttk.Frame(self.ep_form)
        grid.pack(fill="x", pady=4)
        for row, (attr, label, kind, values) in enumerate(fields):
            ttk.Label(grid, text=label, style="Muted.TLabel", font=FONT["small"]).grid(row=row // 3 * 2, column=row % 3, sticky="w", padx=4)
            if kind == "bool":
                var = tk.BooleanVar(value=getattr(ep, attr))
                widget = ttk.Checkbutton(grid, text="Sim", variable=var)
            else:
                var = tk.StringVar(value=getattr(ep, attr))
                widget = ttk.Combobox(grid, textvariable=var, values=values, state="readonly") if kind == "combo" else ttk.Entry(grid, textvariable=var)
            widget.grid(row=row // 3 * 2 + 1, column=row % 3, sticky="ew", padx=4, pady=(0, 4))
            var.trace_add("write", lambda *a, v=var, at=attr: self._set_ep(index, at, v.get()))
        for c in range(3):
            grid.columnconfigure(c, weight=1)
        ttk.Label(self.ep_form, text="Mapeamento para a lista (campo do JSON, campo.sub ou modelo com {campo})",
                  style="Muted.TLabel").pack(anchor="w", padx=4, pady=(6, 0))
        mgrid = ttk.Frame(self.ep_form)
        mgrid.pack(fill="x")
        for col, (key, label) in enumerate([("title", "Título"), ("subtitle", "Subtítulo"), ("image", "Imagem"),
                                             ("price", "Preço"), ("description", "Descrição"), ("id", "Id")]):
            ttk.Label(mgrid, text=label, style="Muted.TLabel", font=FONT["small"]).grid(row=(col // 3) * 2, column=col % 3, sticky="w", padx=4)
            var = tk.StringVar(value=ep.mapping.get(key, ""))
            ttk.Entry(mgrid, textvariable=var).grid(row=(col // 3) * 2 + 1, column=col % 3, sticky="ew", padx=4, pady=(0, 4))
            var.trace_add("write", lambda *a, v=var, k=key: self._set_map(index, k, v.get()))
        for c in range(3):
            mgrid.columnconfigure(c, weight=1)
        ttk.Label(self.ep_form, text="Deixe o mapeamento vazio para escolha automática.", style="Muted.TLabel",
                  font=FONT["small"]).pack(anchor="w", padx=4)

    def _set_ep(self, index, attr, value):
        ep = self.current.endpoints[index]
        if attr == "returns_list":
            value = bool(value) and value not in ("0", "False")
        elif attr == "name":
            value = to_camel(value, "call")
        elif attr == "path":
            value = value.strip().lstrip("/")
        setattr(ep, attr, value)

    def _set_map(self, index, key, value):
        mapping = self.current.endpoints[index].mapping
        if value.strip():
            mapping[key] = value.strip()
        else:
            mapping.pop(key, None)

    # ----- modelos
    def _models_tab(self, parent, api):
        top = ttk.Frame(parent)
        top.pack(fill="both", expand=True)
        left = ttk.Frame(top)
        left.pack(side="left", fill="y")
        self.md_list = tk.Listbox(left, bg=C["panel2"], fg=C["text"], selectbackground=C["accent"], relief="flat",
                                  highlightthickness=0, exportselection=False, width=24)
        self.md_list.pack(fill="y", expand=True)
        self.md_list.bind("<<ListboxSelect>>", lambda e: self.select_model())
        bar = ttk.Frame(left)
        bar.pack(fill="x", pady=4)
        ttk.Button(bar, text="Novo", command=self.add_model).pack(side="left")
        ttk.Button(bar, text="Remover", command=self.remove_model).pack(side="left", padx=4)
        ttk.Button(left, text="Importar de JSON de exemplo...", command=self.import_json).pack(fill="x")
        right = ttk.Frame(top)
        right.pack(side="left", fill="both", expand=True, padx=8)
        self.v_model_name = tk.StringVar()
        ttk.Label(right, text="Nome do modelo", style="Muted.TLabel").pack(anchor="w")
        ttk.Entry(right, textvariable=self.v_model_name).pack(fill="x")
        ttk.Label(right, text="Campos (um por linha: nome:Tipo). Tipos: String, Int, Long, Double, Boolean, "
                              "List<X>, Map<String,Double> ou outro modelo.", style="Muted.TLabel",
                  wraplength=560).pack(anchor="w", pady=(6, 0))
        self.fields_box = text_widget(right, height=12, mono=True)
        self.fields_box.pack(fill="both", expand=True)
        ttk.Button(right, text="Aplicar alterações do modelo", command=self.apply_model).pack(anchor="e", pady=4)
        self.refresh_models()

    def refresh_models(self, select=0):
        self.md_list.delete(0, "end")
        for m in self.current.models:
            self.md_list.insert("end", m.name)
        if self.current.models:
            self.md_list.selection_set(min(select, len(self.current.models) - 1))
            self.select_model()

    def select_model(self):
        sel = self.md_list.curselection()
        if not sel:
            return
        model = self.current.models[sel[0]]
        self.v_model_name.set(model.name)
        self.fields_box.delete("1.0", "end")
        self.fields_box.insert("1.0", fields_to_text(model.fields))

    def apply_model(self):
        sel = self.md_list.curselection()
        if not sel:
            return
        model = self.current.models[sel[0]]
        model.name = to_pascal(self.v_model_name.get(), "Model")
        model.fields = [ApiField(n, ty) for n, ty in parse_fields(self.fields_box.get("1.0", "end"))]
        self.refresh_models(sel[0])

    def add_model(self):
        self.current.models.append(ApiModel(f"Model{len(self.current.models) + 1}", [ApiField("id", "Long"), ApiField("name", "String")]))
        self.refresh_models(len(self.current.models) - 1)

    def remove_model(self):
        sel = self.md_list.curselection()
        if sel:
            del self.current.models[sel[0]]
            self.refresh_models()

    def import_json(self):
        dialog = JsonImportDialog(self)
        result = dialog.show()
        if not result:
            return
        text, root_name = result
        try:
            models, name, returns_list, wrapper = json_infer.infer(text, root_name)
        except Exception as exc:
            messagebox.showerror("JSON inválido", str(exc), parent=self)
            return
        existing = {m.name for m in self.current.models}
        for m in models:
            if m.name in existing:
                self.current.models = [x for x in self.current.models if x.name != m.name]
            self.current.models.append(m)
        if messagebox.askyesno("Criar endpoint", f"Modelos criados: {', '.join(m.name for m in models)}.\n"
                                                 "Criar também um endpoint GET usando este formato?", parent=self):
            self.current.endpoints.append(Endpoint(to_camel("get " + root_name), "GET", "", name, returns_list, wrapper))
            self.refresh_endpoints(len(self.current.endpoints) - 1)
        self.refresh_models(len(self.current.models) - 1)

    def save(self):
        names = [a.name for a in self.apis]
        if len(names) != len(set(names)):
            messagebox.showerror("Nomes repetidos", "Cada API precisa de um nome diferente.", parent=self)
            return
        self.result = self.apis
        self.close()


class JsonImportDialog(Dialog):
    def __init__(self, master):
        super().__init__(master, "Importar modelo de um JSON", 640, 520)
        root = ttk.Frame(self)
        root.pack(fill="both", expand=True, padx=12, pady=12)
        ttk.Label(root, text="Cole uma resposta de exemplo da API (objeto ou lista).", style="Muted.TLabel").pack(anchor="w")
        row = ttk.Frame(root)
        row.pack(fill="x", pady=6)
        ttk.Label(row, text="Nome do modelo principal").pack(side="left")
        self.name = tk.StringVar(value="Item")
        ttk.Entry(row, textvariable=self.name).pack(side="left", fill="x", expand=True, padx=6)
        self.buttons(root, [("Cancelar", self.close, None), ("Importar", self.ok, "Accent.TButton")]).pack(side="bottom", fill="x", pady=(8, 0))
        self.box = text_widget(root, height=16, mono=True)
        self.box.pack(fill="both", expand=True)
        self.box.insert("1.0", '[\n  {"id": 1, "title": "Produto", "price": 9.9, "image": "https://..."}\n]')

    def ok(self):
        self.result = (self.box.get("1.0", "end"), self.name.get() or "Item")
        self.close()


# ======================================================================= banco de dados

class DatabaseEditor(Dialog):
    """Entidades do banco Room, com geracao automatica de telas de cadastro."""

    def __init__(self, master, project):
        super().__init__(master, "Banco de dados local (Room)", 900, 600)
        self.entities = copy.deepcopy(project.entities)
        self.crud = []
        self.project = project
        root = ttk.Frame(self)
        root.pack(fill="both", expand=True, padx=12, pady=12)
        ttk.Label(root, text="Entidades do banco de dados", style="Title.TLabel").pack(anchor="w")
        ttk.Label(root, text="Cada entidade vira uma tabela com id automático, DAO com CRUD e pode ser usada como "
                             "fonte de listas e destino de formulários.", style="Muted.TLabel").pack(anchor="w", pady=(0, 8))
        self.buttons(root, [("Cancelar", self.close, None), ("Salvar", self.save, "Accent.TButton")]).pack(side="bottom", fill="x", pady=(8, 0))
        body = ttk.Frame(root)
        body.pack(fill="both", expand=True)
        left = ttk.Frame(body)
        left.pack(side="left", fill="y")
        self.list = tk.Listbox(left, bg=C["panel2"], fg=C["text"], selectbackground=C["accent"], relief="flat",
                               highlightthickness=0, exportselection=False, width=26, font=FONT["base"])
        self.list.pack(fill="y", expand=True)
        self.list.bind("<<ListboxSelect>>", lambda e: self.select())
        bar = ttk.Frame(left)
        bar.pack(fill="x", pady=4)
        ttk.Button(bar, text="Nova", width=6, command=self.add).pack(side="left")
        ttk.Button(bar, text="Remover", width=8, command=self.remove).pack(side="left", padx=4)
        right = ttk.Frame(body)
        right.pack(side="left", fill="both", expand=True, padx=10)
        self.v_name = tk.StringVar()
        ttk.Label(right, text="Nome da entidade (ex.: Produto, Tarefa)", style="Muted.TLabel").pack(anchor="w")
        ttk.Entry(right, textvariable=self.v_name).pack(fill="x")
        ttk.Label(right, text="Campos, um por linha (nome:Tipo). Tipos: String, Int, Long, Double, Float, Boolean. "
                              "O campo id é criado automaticamente.", style="Muted.TLabel", wraplength=560).pack(anchor="w", pady=(8, 0))
        self.fields = text_widget(right, height=12, mono=True)
        self.fields.pack(fill="both", expand=True)
        actions = ttk.Frame(right)
        actions.pack(fill="x", pady=6)
        ttk.Button(actions, text="Aplicar", command=self.apply).pack(side="left")
        ttk.Button(actions, text="Gerar telas de lista e cadastro", command=self.make_crud).pack(side="left", padx=6)
        self.crud_label = ttk.Label(right, text="", style="Accent.TLabel")
        self.crud_label.pack(anchor="w")
        self.refresh()

    def refresh(self, select=0):
        self.list.delete(0, "end")
        for e in self.entities:
            self.list.insert("end", f"{e.name} ({len(e.fields)} campos)")
        if self.entities:
            self.list.selection_set(min(select, len(self.entities) - 1))
            self.select()

    def select(self):
        sel = self.list.curselection()
        if not sel:
            return
        e = self.entities[sel[0]]
        self.v_name.set(e.name)
        self.fields.delete("1.0", "end")
        self.fields.insert("1.0", fields_to_text(e.fields))

    def apply(self):
        sel = self.list.curselection()
        if not sel:
            return
        e = self.entities[sel[0]]
        e.name = to_pascal(self.v_name.get(), "Item")
        valid = {"String", "Int", "Long", "Double", "Float", "Boolean"}
        e.fields = [[to_camel(n), ty if ty in valid else "String"] for n, ty in parse_fields(self.fields.get("1.0", "end"))
                    if to_camel(n) != "id"]
        self.refresh(sel[0])

    def add(self):
        self.entities.append(Entity(f"Item{len(self.entities) + 1}", [["name", "String"], ["description", "String"], ["price", "Double"]]))
        self.refresh(len(self.entities) - 1)

    def remove(self):
        sel = self.list.curselection()
        if sel:
            del self.entities[sel[0]]
            self.refresh()

    def make_crud(self):
        self.apply()
        sel = self.list.curselection()
        if not sel:
            return
        e = self.entities[sel[0]]
        self.crud.append(e.name)
        self.crud_label.configure(text=f"Telas de {', '.join(self.crud)} serão criadas ao salvar.")

    def save(self):
        self.apply()
        names = [e.name for e in self.entities]
        if len(names) != len(set(names)):
            messagebox.showerror("Nomes repetidos", "Cada entidade precisa de um nome diferente.", parent=self)
            return
        self.result = (self.entities, list(dict.fromkeys(self.crud)))
        self.close()


def crud_screens(entity):
    """Cria uma tela de lista e uma de cadastro para a entidade."""
    from ..catalog.components import default_props
    name = to_pascal(entity.name)
    list_name, form_name = f"Lista{name}", f"Novo{name}"

    def comp(ctype, **props):
        values = default_props(ctype)
        values.update(props)
        return Component(type=ctype, props=values, id=new_id())
    list_screen = Screen(name=list_name, title=f"{entity.name}", in_nav=True, icon="list", components=[
        comp("search_bar", hint=f"Buscar {entity.name.lower()}..."),
        comp("list", source=f"entity:{entity.name}", show_price=any(f[1] in ("Double", "Float") for f in entity.fields)),
        comp("fab", icon="add", action=f"navigate:{form_name}"),
    ])
    fields = []
    for fname, ftype in entity.fields:
        if ftype == "Boolean":
            fields.append(comp("switch", label=fname.capitalize(), key=fname))
        elif ftype in ("Int", "Long", "Double", "Float"):
            fields.append(comp("text_field", label=fname.capitalize(), key=fname, input="number", validation="number"))
        else:
            fields.append(comp("text_field", label=fname.capitalize(), key=fname))
    form_screen = Screen(name=form_name, title=f"Novo {entity.name.lower()}", form_entity=entity.name, icon="add",
                         components=[comp("title", text=f"Cadastrar {entity.name.lower()}", size="medium")] + fields +
                         [comp("button", text="Salvar", action=f"submit:{list_name}")])
    return [list_screen, form_screen]


# ======================================================================= configuracoes do projeto

class ProjectSettings(Dialog):
    """Nome, pacote, interface, SDK, navegacao, cores e idiomas do projeto."""

    def __init__(self, master, project):
        super().__init__(master, "Configurações do projeto", 760, 640)
        self.project = project
        root = ScrollFrame(self)
        root.pack(fill="both", expand=True)
        body = root.body
        self.vars = {}
        self.form_project(body, project)
        bar = self.buttons(self, [("Cancelar", self.close, None), ("Aplicar", self.ok, "Accent.TButton")])
        bar.pack(fill="x", padx=12, pady=10)
        root.bind_children()

    def form_project(self, body, p):
        def section(title):
            tk.Label(body, text=title, bg=C["panel"], fg=C["accent_hover"], font=FONT["h2"]).pack(anchor="w", padx=16, pady=(14, 4))

        def entry(key, label, value):
            tk.Label(body, text=label, bg=C["panel"], fg=C["muted"], font=FONT["small"]).pack(anchor="w", padx=16)
            var = tk.StringVar(value=value)
            ttk.Entry(body, textvariable=var).pack(fill="x", padx=16, pady=(0, 6))
            self.vars[key] = var

        def combo(key, label, values, value):
            tk.Label(body, text=label, bg=C["panel"], fg=C["muted"], font=FONT["small"]).pack(anchor="w", padx=16)
            var = tk.StringVar(value=value)
            ttk.Combobox(body, textvariable=var, values=values, state="readonly").pack(fill="x", padx=16, pady=(0, 6))
            self.vars[key] = var

        section("Identificação")
        entry("name", "Nome do aplicativo", p.name)
        entry("package", "Pacote (applicationId)", p.package)
        entry("description", "Descrição", p.description)
        entry("version_name", "Versão (versionName)", p.version_name)
        entry("version_code", "Código da versão (versionCode)", str(p.version_code))
        section("Interface e compatibilidade")
        combo("ui_mode", "Tecnologia de interface", ["compose - Jetpack Compose", "views - XML com ViewBinding"],
              "compose - Jetpack Compose" if p.ui_mode == "compose" else "views - XML com ViewBinding")
        combo("navigation", "Navegação principal", ["stack - pilha de telas", "bottom - barra inferior", "drawer - menu lateral"],
              {"stack": "stack - pilha de telas", "bottom": "bottom - barra inferior", "drawer": "drawer - menu lateral"}[p.navigation])
        sdks = [f"{api} - {name}" for api, name in SDK_LEVELS]
        combo("min_sdk", "SDK mínimo", sdks, next((s for s in sdks if s.startswith(str(p.min_sdk))), sdks[0]))
        combo("target_sdk", "SDK alvo e de compilação", sdks, next((s for s in sdks if s.startswith(str(p.target_sdk))), sdks[-2]))
        section("Aparência")
        combo("theme_mode", "Tema", ["system - seguir o sistema", "light - sempre claro", "dark - sempre escuro"],
              {"system": "system - seguir o sistema", "light": "light - sempre claro", "dark": "dark - sempre escuro"}[p.theme_mode])
        palettes = tk.Frame(body, bg=C["panel"])
        palettes.pack(fill="x", padx=16, pady=4)
        for i, (name, c1, c2, c3) in enumerate(PALETTES):
            cell = tk.Frame(palettes, bg=C["card"], cursor="hand2")
            cell.grid(row=i // 5, column=i % 5, padx=3, pady=3, sticky="ew")
            swatch = tk.Canvas(cell, width=96, height=22, bg=C["card"], highlightthickness=0)
            swatch.create_rectangle(0, 0, 48, 22, fill=c1, outline="")
            swatch.create_rectangle(48, 0, 72, 22, fill=c2, outline="")
            swatch.create_rectangle(72, 0, 96, 22, fill=c3, outline="")
            swatch.pack(padx=4, pady=(4, 0))
            label = tk.Label(cell, text=name, bg=C["card"], fg=C["text"], font=FONT["small"])
            label.pack(pady=(0, 4))
            for w in (cell, swatch, label):
                w.bind("<Button-1>", lambda e, a=c1, b=c2, c=c3: self.set_colors(a, b, c))
        self.color_buttons = {}
        colors = tk.Frame(body, bg=C["panel"])
        colors.pack(fill="x", padx=16, pady=6)
        for key, label, value in (("primary_color", "Principal", p.primary_color), ("secondary_color", "Secundária", p.secondary_color),
                                  ("tertiary_color", "Destaque", p.tertiary_color)):
            var = tk.StringVar(value=value)
            self.vars[key] = var
            btn = tk.Button(colors, text=f"{label}\n{value}", bg=value, fg="#FFFFFF", relief="flat", width=14,
                            activebackground=value, command=lambda k=key: self.pick(k))
            btn.pack(side="left", padx=4)
            self.color_buttons[key] = btn
        section("Idiomas e permissões")
        tk.Label(body, text="Idiomas (o primeiro é o padrão). Ex.: pt,en,es", bg=C["panel"], fg=C["muted"], font=FONT["small"]).pack(anchor="w", padx=16)
        self.vars["languages"] = tk.StringVar(value=",".join(p.languages))
        ttk.Entry(body, textvariable=self.vars["languages"]).pack(fill="x", padx=16)
        self.vars["perm"] = tk.BooleanVar(value=p.request_permissions_on_start)
        ttk.Checkbutton(body, text="Pedir permissões necessárias ao abrir o app", variable=self.vars["perm"]).pack(anchor="w", padx=16, pady=8)

    def set_colors(self, a, b, c):
        for key, value in (("primary_color", a), ("secondary_color", b), ("tertiary_color", c)):
            self.vars[key].set(value)
            btn = self.color_buttons[key]
            btn.configure(bg=value, activebackground=value, text=btn.cget("text").split("\n")[0] + "\n" + value)

    def pick(self, key):
        color = colorchooser.askcolor(self.vars[key].get(), parent=self, title="Escolher cor")[1]
        if color:
            self.vars[key].set(color.upper())
            btn = self.color_buttons[key]
            btn.configure(bg=color, activebackground=color, text=btn.cget("text").split("\n")[0] + "\n" + color.upper())

    def ok(self):
        v = self.vars
        package = v["package"].get().strip()
        if not is_valid_package(package):
            messagebox.showerror("Pacote inválido", "Use o formato com.empresa.app, só letras minúsculas, números e pontos.", parent=self)
            return
        try:
            code = int(v["version_code"].get())
        except ValueError:
            messagebox.showerror("Versão inválida", "O código da versão deve ser um número inteiro.", parent=self)
            return
        self.result = {
            "name": v["name"].get().strip() or "MeuApp", "package": package, "description": v["description"].get(),
            "version_name": v["version_name"].get().strip() or "1.0.0", "version_code": code,
            "ui_mode": v["ui_mode"].get().split(" ")[0], "navigation": v["navigation"].get().split(" ")[0],
            "min_sdk": int(v["min_sdk"].get().split(" ")[0]), "target_sdk": int(v["target_sdk"].get().split(" ")[0]),
            "theme_mode": v["theme_mode"].get().split(" ")[0], "primary_color": v["primary_color"].get(),
            "secondary_color": v["secondary_color"].get(), "tertiary_color": v["tertiary_color"].get(),
            "languages": [x.strip() for x in v["languages"].get().split(",") if x.strip()] or ["pt"],
            "request_permissions_on_start": v["perm"].get(),
        }
        self.result["compile_sdk"] = self.result["target_sdk"]
        if self.result["min_sdk"] > self.result["target_sdk"]:
            messagebox.showerror("SDK inválido", "O SDK mínimo não pode ser maior que o SDK alvo.", parent=self)
            return
        self.close()


class AppSettings(Dialog):
    """Preferencias do DroidBlocks: pasta de saida e versoes das bibliotecas."""

    def __init__(self, master, settings):
        super().__init__(master, "Configurações do DroidBlocks", 760, 620)
        self.settings = settings
        root = ttk.Frame(self)
        root.pack(fill="both", expand=True, padx=12, pady=12)
        ttk.Label(root, text="Pasta padrão dos projetos gerados", style="Muted.TLabel").pack(anchor="w")
        row = ttk.Frame(root)
        row.pack(fill="x")
        self.out = tk.StringVar(value=settings["output_dir"])
        ttk.Entry(row, textvariable=self.out).pack(side="left", fill="x", expand=True)
        ttk.Button(row, text="Escolher...", command=self.choose).pack(side="left", padx=4)
        self.autosave = tk.BooleanVar(value=settings["autosave"])
        ttk.Checkbutton(root, text="Salvar automaticamente o projeto a cada alteração", variable=self.autosave).pack(anchor="w", pady=4)
        self.open_after = tk.BooleanVar(value=settings["open_folder_after_generate"])
        ttk.Checkbutton(root, text="Abrir a pasta ao terminar a geração", variable=self.open_after).pack(anchor="w")
        ttk.Label(root, text="Versões (Gradle, Kotlin e bibliotecas). Duplo clique para editar.",
                  style="H2.TLabel").pack(anchor="w", pady=(12, 4))
        frame = ttk.Frame(root)
        frame.pack(fill="both", expand=True)
        self.tree = ttk.Treeview(frame, columns=("k", "v", "d"), show="headings")
        for col, text, width in (("k", "Chave", 200), ("v", "Versão em uso", 160), ("d", "Padrão", 160)):
            self.tree.heading(col, text=text)
            self.tree.column(col, width=width)
        scroll = ttk.Scrollbar(frame, orient="vertical", command=self.tree.yview)
        self.tree.configure(yscrollcommand=scroll.set)
        self.tree.pack(side="left", fill="both", expand=True)
        scroll.pack(side="right", fill="y")
        self.versions = dict(DEFAULT_VERSIONS)
        self.versions.update(settings["versions"] or {})
        self.fill()
        self.tree.bind("<Double-Button-1>", self.edit)
        bar = ttk.Frame(root)
        bar.pack(fill="x", pady=(8, 0))
        ttk.Button(bar, text="Restaurar padrões", command=self.reset).pack(side="left")
        ttk.Button(bar, text="Salvar", style="Accent.TButton", command=self.ok).pack(side="right")
        ttk.Button(bar, text="Cancelar", command=self.close).pack(side="right", padx=4)

    def fill(self):
        self.tree.delete(*self.tree.get_children())
        for key in sorted(self.versions):
            self.tree.insert("", "end", iid=key, values=(key, self.versions[key], DEFAULT_VERSIONS.get(key, "")))

    def edit(self, event):
        item = self.tree.identify_row(event.y)
        if not item:
            return
        x, y, w, h = self.tree.bbox(item, "v")
        var = tk.StringVar(value=self.versions[item])
        entry = ttk.Entry(self.tree, textvariable=var)
        entry.place(x=x, y=y, width=w, height=h)
        entry.focus_set()

        def done(_=None):
            value = var.get().strip()
            if value:
                self.versions[item] = value
            entry.destroy()
            self.fill()
        entry.bind("<Return>", done)
        entry.bind("<FocusOut>", done)

    def reset(self):
        self.versions = dict(DEFAULT_VERSIONS)
        self.fill()

    def choose(self):
        folder = filedialog.askdirectory(parent=self, initialdir=self.out.get())
        if folder:
            self.out.set(folder)

    def ok(self):
        self.settings.data["output_dir"] = self.out.get()
        self.settings.data["autosave"] = self.autosave.get()
        self.settings.data["open_folder_after_generate"] = self.open_after.get()
        self.settings.data["versions"] = {k: v for k, v in self.versions.items() if DEFAULT_VERSIONS.get(k) != v}
        self.settings.save()
        self.result = True
        self.close()


# ======================================================================= codigo

class CodePreview(Dialog):
    """Navegador de todos os arquivos que serao gerados."""

    def __init__(self, master, result, focus=None):
        super().__init__(master, "Pré-visualização do código gerado", 1180, 760)
        self.result = None
        self.files = result.files
        root = ttk.PanedWindow(self, orient="horizontal")
        root.pack(fill="both", expand=True, padx=8, pady=8)
        left = ttk.Frame(root)
        self.tree = ttk.Treeview(left, show="tree")
        scroll = ttk.Scrollbar(left, orient="vertical", command=self.tree.yview)
        self.tree.configure(yscrollcommand=scroll.set)
        self.tree.pack(side="left", fill="both", expand=True)
        scroll.pack(side="right", fill="y")
        root.add(left, weight=1)
        right = ttk.Frame(root)
        self.path_label = ttk.Label(right, text="", style="Muted.TLabel")
        self.path_label.pack(anchor="w")
        self.text = text_widget(right, height=30, mono=True)
        xs = ttk.Scrollbar(right, orient="horizontal", command=self.text.xview)
        ys = ttk.Scrollbar(right, orient="vertical", command=self.text.yview)
        self.text.configure(xscrollcommand=xs.set, yscrollcommand=ys.set)
        ys.pack(side="right", fill="y")
        self.text.pack(fill="both", expand=True)
        xs.pack(fill="x")
        root.add(right, weight=3)
        self._highlight_tags()
        nodes = {}
        for path in self.files:
            parts = path.split("/")
            parent = ""
            for i, part in enumerate(parts):
                key = "/".join(parts[:i + 1])
                if key not in nodes:
                    nodes[key] = self.tree.insert(parent, "end", iid=key, text=part, open=i < 1)
                parent = key
        self.tree.bind("<<TreeviewSelect>>", lambda e: self.show_file())
        target = focus if focus in self.files else next((p for p in self.files if p.endswith("MainActivity.kt")), None)
        if target:
            self.tree.see(target)
            self.tree.selection_set(target)
        info = f"{len(self.files)} arquivos  |  {sum(1 for p in self.files if p.endswith('.kt'))} arquivos Kotlin"
        ttk.Label(self, text=info, style="Muted.TLabel").pack(anchor="w", padx=10, pady=(0, 8))

    def _highlight_tags(self):
        self.text.tag_configure("kw", foreground="#7AB7FF")
        self.text.tag_configure("str", foreground="#A5D6A7")
        self.text.tag_configure("com", foreground="#6B7C96")
        self.text.tag_configure("ann", foreground="#FFB86C")

    def show_file(self):
        sel = self.tree.selection()
        if not sel or sel[0] not in self.files:
            return
        content = self.files[sel[0]]
        self.path_label.configure(text=sel[0])
        self.text.configure(state="normal")
        self.text.delete("1.0", "end")
        if isinstance(content, bytes):
            self.text.insert("1.0", f"[arquivo binário: {len(content)} bytes]")
        else:
            self.text.insert("1.0", content)
            if sel[0].endswith((".kt", ".kts")):
                highlight(self.text)
        self.text.configure(state="disabled")


KEYWORDS = r"\m(package|import|class|object|fun|val|var|if|else|when|return|private|override|data|interface|suspend|companion|abstract|true|false|null|for|in|is|as|try|catch|throw|this|by)\M"


def highlight(text):
    """Realce de sintaxe simples para Kotlin."""
    for tag, pattern in (("kw", KEYWORDS), ("ann", r"@\w+"), ("str", r'"[^"\n]*"'), ("com", r"//[^\n]*|/\*\*?[^*]*\*+/")):
        start = "1.0"
        count = tk.IntVar()
        while True:
            pos = text.search(pattern, start, "end", regexp=True, count=count)
            if not pos or count.get() == 0:
                break
            end = f"{pos}+{count.get()}c"
            text.tag_add(tag, pos, end)
            start = end


# ======================================================================= geracao

class GenerateDialog(Dialog):
    """Gera o projeto Android em disco (pasta e .zip opcional)."""

    def __init__(self, master, app):
        super().__init__(master, "Gerar projeto Android Studio", 720, 560)
        self.app = app
        root = ttk.Frame(self)
        root.pack(fill="both", expand=True, padx=14, pady=14)
        project = app.project
        ttk.Label(root, text=f"Gerar {project.name}", style="Title.TLabel").pack(anchor="w")
        ttk.Label(root, text=f"Pacote {project.package}  |  {len(project.screens)} telas  |  "
                             f"{'Jetpack Compose' if project.ui_mode == 'compose' else 'XML Views'}",
                  style="Muted.TLabel").pack(anchor="w", pady=(0, 10))
        ttk.Label(root, text="Pasta de destino").pack(anchor="w")
        row = ttk.Frame(root)
        row.pack(fill="x")
        self.out = tk.StringVar(value=app.settings["output_dir"])
        ttk.Entry(row, textvariable=self.out).pack(side="left", fill="x", expand=True)
        ttk.Button(row, text="Escolher...", command=self.choose).pack(side="left", padx=4)
        self.zip = tk.BooleanVar(value=True)
        ttk.Checkbutton(root, text="Também criar arquivo .zip", variable=self.zip).pack(anchor="w", pady=(8, 0))
        self.open_after = tk.BooleanVar(value=app.settings["open_folder_after_generate"])
        ttk.Checkbutton(root, text="Abrir a pasta ao terminar", variable=self.open_after).pack(anchor="w")
        self.progress = ttk.Progressbar(root, mode="determinate")
        self.progress.pack(fill="x", pady=10)
        self.log = text_widget(root, height=12)
        self.log.pack(fill="both", expand=True)
        bar = ttk.Frame(root)
        bar.pack(fill="x", pady=(10, 0))
        self.gen_button = ttk.Button(bar, text="Gerar agora", style="Accent.TButton", command=self.run)
        self.gen_button.pack(side="right")
        ttk.Button(bar, text="Fechar", command=self.close).pack(side="right", padx=4)
        # Acoes disponiveis depois que o projeto foi gerado.
        self.studio_button = ttk.Button(bar, text="Abrir no Android Studio", command=self.open_studio)
        self.studio_button.pack(side="left")
        self.build_button = ttk.Button(bar, text="Compilar APK", command=self.toggle_build)
        self.build_button.pack(side="left", padx=4)
        self.studio_button.state(["disabled"])
        self.build_button.state(["disabled"])
        self.root_dir = None
        self.process = None
        self.write("Pronto para gerar. Os diagnósticos aparecem abaixo:\n")
        for level, message in app.resolved().diagnostics:
            self.write(f"[{level}] {t(message)}\n")

    def write(self, text):
        self.log.configure(state="normal")
        self.log.insert("end", text)
        self.log.see("end")
        self.log.configure(state="disabled")

    def choose(self):
        folder = filedialog.askdirectory(parent=self, initialdir=self.out.get())
        if folder:
            self.out.set(folder)

    def run(self):
        errors = self.app.resolved().errors
        if errors:
            messagebox.showerror("Corrija os erros", "\n".join(t(e) for e in errors), parent=self)
            return
        out = Path(self.out.get()).expanduser()
        self.gen_button.state(["disabled"])
        self.progress.configure(mode="indeterminate")
        self.progress.start(12)
        self.write(f"\nGerando em {out} ...\n")
        project = self.app.project.clone()
        versions = self.app.settings["versions"] or {}

        def work():
            try:
                result = generate(project, versions)
                root = write_project(result, out)
                zip_path = None
                if self.zip.get():
                    zip_path = zip_project(result, out / f"{result.folder_name}.zip")
                self.after(0, lambda: self.done(result, root, zip_path, None))
            except Exception as exc:
                self.after(0, lambda e=exc: self.done(None, None, None, e))
        threading.Thread(target=work, daemon=True).start()

    def done(self, result, root, zip_path, error):
        self.progress.stop()
        self.progress.configure(mode="determinate", value=0 if error else 100)
        self.gen_button.state(["!disabled"])
        if error:
            self.write(f"\nFalha: {error}\n")
            messagebox.showerror("Falha na geração", str(error), parent=self)
            return
        kt = sum(1 for p in result.files if p.endswith(".kt"))
        self.write(f"\nConcluído: {len(result.files)} arquivos ({kt} em Kotlin).\nPasta: {root}\n")
        if zip_path:
            self.write(f"Zip: {zip_path}\n")
        self.write("\nAbra a pasta no Android Studio (File > Open) e aguarde a sincronização do Gradle.\n")
        self.app.settings["output_dir"] = self.out.get()
        self.app.log(f"Projeto gerado em {root}")
        self.root_dir = root
        self.studio_button.state(["!disabled"])
        self.build_button.state(["!disabled"])
        self.write("\nFerramentas encontradas neste computador:\n")
        for name, value in android_tools.environment_report():
            self.write(f"  {name}: {t(value)}\n")
        if self.open_after.get():
            open_folder(root)

    def open_studio(self):
        if not self.root_dir:
            return
        if android_tools.open_in_studio(self.root_dir):
            self.write("\nAbrindo no Android Studio...\n")
        else:
            messagebox.showinfo("Android Studio não encontrado",
                                "Não encontrei o Android Studio nas pastas padrão.\n\n"
                                f"Abra-o manualmente e use File > Open em:\n{self.root_dir}", parent=self)

    def toggle_build(self):
        """Inicia a compilacao do APK de depuracao ou interrompe a que esta em andamento."""
        if self.process is not None:
            self.process.terminate()
            self.write("\nCompilação interrompida.\n")
            return
        try:
            self.process = android_tools.start_build(self.root_dir)
        except (RuntimeError, OSError) as exc:
            messagebox.showwarning("Não foi possível compilar", t(str(exc)), parent=self)
            return
        self.write("\nCompilando com o Gradle (assembleDebug). Na primeira vez o Gradle baixa a si mesmo e as "
                   "bibliotecas, então é preciso internet e pode levar alguns minutos.\n\n")
        self.build_button.configure(text="Parar compilação")
        self.progress.configure(mode="indeterminate")
        self.progress.start(12)
        process = self.process

        def pump():
            for line in process.stdout:
                self.after(0, lambda text=line: self.write(text))
            code = process.wait()
            self.after(0, lambda: self.build_finished(code))
        threading.Thread(target=pump, daemon=True).start()

    def build_finished(self, code):
        self.process = None
        self.progress.stop()
        self.progress.configure(mode="determinate", value=100 if code == 0 else 0)
        try:
            self.build_button.configure(text="Compilar APK")
        except tk.TclError:
            return
        apk = android_tools.apk_path(self.root_dir)
        if code == 0 and apk.exists():
            self.write(f"\nAPK gerado: {apk}\nInstale no celular ou emulador (adb install).\n")
            self.app.log(f"APK compilado: {apk}")
            open_folder(apk.parent)
        elif code != 0:
            self.write(f"\nO Gradle terminou com código {code}. Veja as mensagens acima.\n")

    def close(self):
        if self.process is not None:
            self.process.terminate()
        super().close()


class AboutDialog(Dialog):
    def __init__(self, master):
        from .. import __version__, APP_NAME
        super().__init__(master, "Sobre", 520, 380)
        root = ttk.Frame(self)
        root.pack(fill="both", expand=True, padx=20, pady=20)
        ttk.Label(root, text=APP_NAME, style="Title.TLabel").pack(anchor="w")
        ttk.Label(root, text=f"Versão {__version__}", style="Muted.TLabel").pack(anchor="w")
        from ..catalog.features import ALL_FEATURES
        from ..catalog.algorithms import ALGORITHMS_LIST
        from ..catalog.components import COMPONENT_LIST
        info = (f"Construtor no-code de aplicativos Android em Kotlin, 100% offline.\n\n"
                f"{len(COMPONENT_LIST)} blocos visuais\n{len(ALL_FEATURES)} funcionalidades\n"
                f"{len(ALGORITHMS_LIST)} algoritmos\n{len(template_catalog.TEMPLATES)} modelos de aplicativos\n"
                f"{len(api_presets.PRESETS)} APIs públicas prontas\n\n"
                "Gera projetos completos para o Android Studio: Gradle (Kotlin DSL), catálogo de versões, "
                "manifesto, telas em Jetpack Compose ou XML, ViewModels, Room, Retrofit, testes e documentação.")
        tk.Label(root, text=info, bg=C["panel"], fg=C["text"], justify="left", wraplength=460).pack(anchor="w", pady=12)
        ttk.Button(root, text="Fechar", command=self.close).pack(anchor="e")
