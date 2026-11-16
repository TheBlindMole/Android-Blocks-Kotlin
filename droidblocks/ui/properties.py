"""Painel direito: propriedades do bloco ou da tela selecionada."""

import tkinter as tk
from tkinter import ttk

from ..catalog.components import COMPONENTS, ACTION_LIST, ACTIONS, ICON_NAMES, parse_action, split_actions, join_actions
from ..catalog import features as feature_catalog
from .theme import C, FONT, ScrollFrame, text_widget
from .text import t

CHOICE_LABELS = {
    "large": "Grande", "medium": "Média", "small": "Pequena", "start": "Esquerda", "center": "Centro",
    "body": "Corpo", "caption": "Legenda", "emphasis": "Destaque", "filled": "Preenchido",
    "outlined": "Contorno", "tonal": "Tonal", "text": "Texto", "url": "URL", "photo": "Foto do usuário",
    "bar": "Barras", "line": "Linhas", "pie": "Pizza", "linear": "Linear", "circular": "Circular",
    "stopwatch": "Cronômetro", "countdown": "Contagem regressiva", "email": "E-mail", "number": "Número",
    "phone": "Telefone", "password": "Senha", "multiline": "Várias linhas", "none": "Nenhuma",
    "required": "Obrigatório", "cpf": "CPF", "cnpj": "CNPJ", "nif": "NIF (Portugal)", "cep": "CEP",
    "postal_pt": "Código postal (PT)",
}


def source_options(project):
    """Fontes de dados disponiveis para listas: (rotulo, valor)."""
    options = [("Exemplo: genérico", "sample:default")]
    for name in sorted(project.samples):
        if name != "default":
            options.append((f"Exemplo: {name}", f"sample:{name}"))
    for entity in project.entities:
        options.append((f"Banco: {entity.name}", f"entity:{entity.name}"))
    for api in project.apis:
        for ep in api.endpoints:
            if (ep.method or "GET").upper() == "GET":
                options.append((f"API: {api.name}.{ep.name}", f"api:{api.name}.{ep.name}"))
    options += [("Carrinho", "cart"), ("Favoritos", "favorites"), ("Chat", "chat"), ("Contatos do aparelho", "contacts")]
    return options


class PropertiesPanel(ttk.Frame):
    def __init__(self, master, app):
        super().__init__(master)
        self.app = app
        self.header = ttk.Label(self, text="Propriedades", style="H2.TLabel")
        self.header.pack(anchor="w", padx=12, pady=(10, 0))
        self.subheader = ttk.Label(self, text="", style="Muted.TLabel", wraplength=280, justify="left")
        self.subheader.pack(anchor="w", padx=12, pady=(2, 6))
        self.scroll = ScrollFrame(self)
        self.scroll.pack(fill="both", expand=True)
        self.first_widget = None

    def clear(self):
        for child in self.scroll.body.winfo_children():
            child.destroy()
        self.first_widget = None

    def show(self):
        self.clear()
        screen = self.app.current_screen()
        comp = self.app.selected_component()
        if comp is not None:
            self._component(comp)
        elif screen is not None:
            self._screen(screen)
        else:
            self.header.configure(text="Propriedades")
            self.subheader.configure(text="Crie uma tela para começar.")
        self.scroll.bind_children()
        self.scroll.canvas.yview_moveto(0)

    # ------------------------------------------------------------ utilitarios de formulario

    def _row(self, label, hint=None):
        frame = tk.Frame(self.scroll.body, bg=C["panel"])
        frame.pack(fill="x", padx=12, pady=(6, 0))
        tk.Label(frame, text=label, bg=C["panel"], fg=C["muted"], font=FONT["small"], anchor="w").pack(fill="x")
        if hint:
            tk.Label(frame, text=hint, bg=C["panel"], fg=C["dim"], font=FONT["small"], anchor="w",
                     wraplength=270, justify="left").pack(fill="x")
        return frame

    def _entry(self, parent, value, on_change):
        var = tk.StringVar(value=str(value))
        entry = ttk.Entry(parent, textvariable=var)
        entry.pack(fill="x", pady=(2, 0))
        var.trace_add("write", lambda *a: on_change(var.get()))
        self.first_widget = self.first_widget or entry
        return entry

    def _combo(self, parent, labels, current_label, on_change, editable=False):
        var = tk.StringVar(value=current_label)
        combo = ttk.Combobox(parent, textvariable=var, values=labels, state="normal" if editable else "readonly")
        combo.pack(fill="x", pady=(2, 0))
        combo.bind("<<ComboboxSelected>>", lambda e: on_change(var.get()))
        if editable:
            var.trace_add("write", lambda *a: on_change(var.get()))
        self.first_widget = self.first_widget or combo
        return combo

    # ------------------------------------------------------------ bloco

    def _component(self, comp):
        spec = COMPONENTS[comp.type]
        self.header.configure(text=t(spec.label))
        self.subheader.configure(text=t(spec.description))
        for prop in spec.props:
            value = comp.props.get(prop.key, prop.default)
            row = self._row(t(prop.label))
            setter = (lambda k: (lambda v: self.app.update_prop(comp, k, v)))(prop.key)
            if prop.kind in ("text",):
                self._entry(row, value, setter)
            elif prop.kind == "multiline":
                box = text_widget(row, height=4)
                box.insert("1.0", str(value))
                box.pack(fill="x", pady=(2, 0))
                box.bind("<KeyRelease>", lambda e, b=box, s=setter: s(b.get("1.0", "end-1c")))
            elif prop.kind == "int":
                self._entry(row, value, lambda v, s=setter: s(int(v)) if v.strip().lstrip("-").isdigit() else None)
            elif prop.kind == "float":
                def to_float(v, s=setter):
                    try:
                        s(float(v.replace(",", ".")))
                    except ValueError:
                        pass
                self._entry(row, value, to_float)
            elif prop.kind == "bool":
                var = tk.BooleanVar(value=bool(value))
                ttk.Checkbutton(row, text="Sim", variable=var, command=lambda v=var, s=setter: s(v.get())).pack(anchor="w")
            elif prop.kind == "choice":
                labels = [CHOICE_LABELS.get(o, o) for o in prop.options]
                mapping = dict(zip(labels, prop.options))
                self._combo(row, labels, CHOICE_LABELS.get(value, value), lambda v, m=mapping, s=setter: s(m.get(v, v)))
            elif prop.kind == "icon":
                self._combo(row, ICON_NAMES, value, setter)
            elif prop.kind == "action":
                self._action_editor(row, comp, prop.key, value)
            elif prop.kind == "source":
                options = source_options(self.app.project)
                labels = [o[0] for o in options]
                mapping = dict(options)
                reverse = {v: k for k, v in options}
                self._combo(row, labels, reverse.get(value, value), lambda v, m=mapping, s=setter: s(m.get(v, v)))
        actions = tk.Frame(self.scroll.body, bg=C["panel"])
        actions.pack(fill="x", padx=12, pady=14)
        ttk.Button(actions, text="Subir", width=6, command=lambda: self.app.shift_selected(-1)).pack(side="left")
        ttk.Button(actions, text="Descer", width=7, command=lambda: self.app.shift_selected(1)).pack(side="left", padx=4)
        ttk.Button(actions, text="Duplicar", width=9, command=self.app.duplicate_selected).pack(side="left")
        ttk.Button(actions, text="Excluir", width=8, style="Danger.TButton", command=self.app.delete_selected).pack(side="right")
        if spec.requires:
            names = ", ".join(t(feature_catalog.FEATURES[r].name) for r in spec.requires)
            tk.Label(self.scroll.body, text=f"Este bloco ativa automaticamente: {names}", bg=C["panel"],
                     fg=C["success"], font=FONT["small"], wraplength=270, justify="left").pack(anchor="w", padx=12)

    def _action_editor(self, parent, comp, prop_key, value):
        """Editor de acoes: uma ou varias acoes executadas em sequencia."""
        steps = [list(parse_action(part)) for part in split_actions(value)] or [["none", ""]]
        labels = [t(a.label) for a in ACTION_LIST]
        by_label = {t(a.label): a.key for a in ACTION_LIST}
        box = tk.Frame(parent, bg=C["panel"])
        box.pack(fill="x")

        def commit():
            parts = [f"{k}:{a}" if a else k for k, a in steps]
            self.app.update_prop(comp, prop_key, join_actions(parts))

        def arg_widget(frame, step):
            action = ACTIONS[step[0]]
            if action.arg == "none":
                return
            label = {"screen": "Tela de destino", "text": "Texto / valor", "url": "Endereço (URL)",
                     "endpoint": "Endpoint da API"}[action.arg]
            tk.Label(frame, text=label, bg=C["panel"], fg=C["dim"], font=FONT["small"], anchor="w").pack(fill="x", pady=(2, 0))
            if action.arg in ("screen", "endpoint"):
                if action.arg == "screen":
                    names = [""] + [sc.name for sc in self.app.project.screens]
                else:
                    names = [f"{a.name}.{e.name}" for a in self.app.project.apis for e in a.endpoints]
                combo = ttk.Combobox(frame, values=names, state="readonly")
                combo.set(step[1])
                combo.pack(fill="x")
                combo.bind("<<ComboboxSelected>>", lambda e: (step.__setitem__(1, combo.get()), commit()))
                if action.arg == "endpoint" and not names:
                    tk.Label(frame, text="Nenhuma API cadastrada. Use o botão APIs.", bg=C["panel"],
                             fg=C["warning"], font=FONT["small"]).pack(anchor="w")
            else:
                var = tk.StringVar(value=step[1])
                ttk.Entry(frame, textvariable=var).pack(fill="x")
                var.trace_add("write", lambda *a: (step.__setitem__(1, var.get()), commit()))

        def render():
            for child in box.winfo_children():
                child.destroy()
            chained = len(steps) > 1
            for index, step in enumerate(steps):
                frame = tk.Frame(box, bg=C["panel"], highlightthickness=1 if chained else 0,
                                 highlightbackground=C["border"])
                frame.pack(fill="x", pady=(2, 2), ipadx=4 if chained else 0, ipady=2 if chained else 0)
                top = tk.Frame(frame, bg=C["panel"])
                top.pack(fill="x")
                if chained:
                    tk.Label(top, text=f"{index + 1}.", bg=C["panel"], fg=C["accent"], font=FONT["bold"],
                             width=3, anchor="w").pack(side="left")
                    ttk.Button(top, text="x", width=2,
                               command=lambda i=index: (steps.pop(i), commit(), render())).pack(side="right")
                    if index > 0:
                        ttk.Button(top, text="^", width=2,
                                   command=lambda i=index: (steps.insert(i - 1, steps.pop(i)), commit(),
                                                            render())).pack(side="right", padx=(0, 2))
                combo = ttk.Combobox(top, values=labels, state="readonly")
                combo.set(t(ACTIONS[step[0]].label))
                combo.pack(side="left", fill="x", expand=True)

                def on_action(_, st=step, cb=combo):
                    st[0] = by_label.get(cb.get(), "none")
                    st[1] = ""
                    commit()
                    render()
                combo.bind("<<ComboboxSelected>>", on_action)
                arg_widget(frame, step)
                feature = ACTIONS[step[0]].feature
                if feature:
                    tk.Label(frame, text=f"Ativa automaticamente: {t(feature_catalog.FEATURES[feature].name)}",
                             bg=C["panel"], fg=C["success"], font=FONT["small"], wraplength=260,
                             justify="left", anchor="w").pack(fill="x")
            if steps[-1][0] != "none":
                ttk.Button(box, text="+ Ação em sequência",
                           command=lambda: (steps.append(["none", ""]), render())).pack(anchor="w", pady=(4, 0))
            if chained:
                tk.Label(box, text="As ações rodam na ordem acima. Depois de login, envio ou leitura de código, "
                                   "as seguintes só rodam se der certo.", bg=C["panel"], fg=C["muted"],
                         font=FONT["small"], wraplength=260, justify="left", anchor="w").pack(fill="x", pady=(2, 0))
        render()

    # ------------------------------------------------------------ tela

    def _screen(self, screen):
        project = self.app.project
        self.header.configure(text=f"Tela: {screen.title or screen.name}")
        self.subheader.configure(text=f"{len(screen.components)} blocos. Clique em um bloco para editá-lo.")
        row = self._row("Nome interno (classe e rota)", "Sem espaços. Ex.: Inicio, Detalhe, Carrinho")
        entry = self._entry(row, screen.name, lambda v: None)
        entry.bind("<FocusOut>", lambda e: self.app.rename_screen(screen, entry.get()))
        entry.bind("<Return>", lambda e: self.app.rename_screen(screen, entry.get()))
        row = self._row("Título exibido")
        self._entry(row, screen.title, lambda v: self.app.update_screen(screen, "title", v))
        row = self._row("Ícone no menu")
        self._combo(row, ICON_NAMES, screen.icon, lambda v: self.app.update_screen(screen, "icon", v))
        row = self._row("Navegação")
        var = tk.BooleanVar(value=screen.in_nav)
        ttk.Checkbutton(row, text="Mostrar no menu principal (barra inferior ou lateral)", variable=var,
                        command=lambda: self.app.update_screen(screen, "in_nav", var.get())).pack(anchor="w")
        row = self._row("Formulário salva em", "Ao usar a ação 'Enviar formulário', os campos com o mesmo nome "
                                                "dos campos da entidade são salvos no banco.")
        entities = [""] + [e.name for e in project.entities]
        self._combo(row, entities, screen.form_entity, lambda v: self.app.update_screen(screen, "form_entity", v))
        start = project.get_start_screen()
        row = self._row("Tela inicial")
        if screen is start:
            tk.Label(row, text="Esta é a tela inicial do app.", bg=C["panel"], fg=C["success"]).pack(anchor="w")
        else:
            ttk.Button(row, text="Definir como tela inicial", command=lambda: self.app.set_start_screen(screen)).pack(anchor="w", pady=2)
        actions = tk.Frame(self.scroll.body, bg=C["panel"])
        actions.pack(fill="x", padx=12, pady=16)
        ttk.Button(actions, text="Duplicar tela", width=13, command=self.app.duplicate_screen).pack(side="left")
        ttk.Button(actions, text="Excluir tela", width=12, style="Danger.TButton", command=self.app.delete_screen).pack(side="right")
        tips = ("Dicas:\n- Arraste blocos da paleta para o celular.\n- Arraste um bloco para reordenar.\n"
                "- Clique com o botão direito em um bloco para mais opções.\n- Delete remove, Ctrl+D duplica.")
        tk.Label(self.scroll.body, text=tips, bg=C["panel"], fg=C["dim"], font=FONT["small"], justify="left",
                 anchor="w").pack(fill="x", padx=12)
