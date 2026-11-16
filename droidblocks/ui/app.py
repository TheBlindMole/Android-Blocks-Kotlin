"""Janela principal do DroidBlocks Studio e controlador do projeto aberto."""

import copy
import json
import tkinter as tk
from pathlib import Path
from tkinter import ttk, filedialog, messagebox

from .. import APP_NAME
from ..catalog.components import COMPONENTS, default_props
from ..catalog import templates as template_catalog
from ..core.model import Project, Screen, Component, new_id
from ..core.naming import to_pascal
from ..core.resolver import resolve, auto_organize
from ..core.storage import Settings, save_project, load_project, PROJECT_EXT
from ..core.generator import generate
from ..core.png import render_icon
from . import theme
from .theme import C, FONT, Tooltip, text_widget
from .text import t
from .canvas import ScreenCanvas
from .tools import NavigationMap, ScreenLibrary
from .palette import BlockPalette, CatalogBrowser
from .properties import PropertiesPanel
from .welcome import WelcomeFrame
from .dialogs import (TemplateGallery, ApiEditor, DatabaseEditor, ProjectSettings, AppSettings, CodePreview,
                      GenerateDialog, AboutDialog, crud_screens, highlight)


class EditorFrame(tk.Frame):
    """Editor: barra de ferramentas, paleta, celular, propriedades e painel inferior."""

    def __init__(self, master, app):
        super().__init__(master, bg=C["bg"])
        self.app = app
        self._toolbar()
        vertical = ttk.PanedWindow(self, orient="vertical")
        vertical.pack(fill="both", expand=True)
        horizontal = ttk.PanedWindow(vertical, orient="horizontal")
        vertical.add(horizontal, weight=5)

        # Esquerda: paleta
        left = ttk.Notebook(horizontal, width=290)
        self.palette = BlockPalette(left, app)
        self.features = CatalogBrowser(left, app, "features")
        self.algorithms = CatalogBrowser(left, app, "algorithms")
        left.add(self.palette, text="Blocos")
        left.add(self.features, text="Funcionalidades")
        left.add(self.algorithms, text="Algoritmos")
        horizontal.add(left, weight=0)

        # Centro: abas de telas + celular
        center = tk.Frame(horizontal, bg=C["bg"])
        self.screen_bar = tk.Frame(center, bg=C["bg"], height=30)
        self.screen_bar.pack(fill="x", padx=8, pady=(8, 4))
        self.screen_bar.bind("<Configure>", self.reflow_screens)
        self._view_bar(center)
        self.canvas = ScreenCanvas(center, app)
        self.canvas.pack(fill="both", expand=True)
        horizontal.add(center, weight=3)

        # Direita: propriedades
        self.properties = PropertiesPanel(horizontal, app)
        horizontal.add(self.properties, weight=0)

        # Inferior: diagnostico, codigo, registro
        bottom = ttk.Notebook(vertical, height=150)
        self.diag_tree = ttk.Treeview(bottom, columns=("level", "msg"), show="headings")
        self.diag_tree.heading("level", text="Tipo")
        self.diag_tree.heading("msg", text="Mensagem")
        self.diag_tree.column("level", width=70, stretch=False)
        self.diag_tree.column("msg", width=900)
        self.diag_tree.tag_configure("erro", foreground=C["error"])
        self.diag_tree.tag_configure("aviso", foreground=C["warning"])
        self.diag_tree.tag_configure("info", foreground=C["muted"])
        bottom.add(self.diag_tree, text="Diagnóstico")
        code_frame = ttk.Frame(bottom)
        top = ttk.Frame(code_frame)
        top.pack(fill="x")
        self.code_file = ttk.Combobox(top, state="readonly", width=70)
        self.code_file.pack(side="left", padx=4, pady=4)
        self.code_file.bind("<<ComboboxSelected>>", lambda e: self.show_code_file())
        ttk.Button(top, text="Atualizar", command=self.app.refresh_code).pack(side="left")
        ttk.Button(top, text="Ver projeto completo", command=self.app.preview_code).pack(side="left", padx=4)
        self.code_text = text_widget(code_frame, height=8, mono=True)
        self.code_text.pack(fill="both", expand=True)
        bottom.add(code_frame, text="Código da tela")
        self.log_text = text_widget(bottom, height=8)
        bottom.add(self.log_text, text="Registro")
        self.bottom = bottom
        vertical.add(bottom, weight=1)
        self.code_cache = {}

        self.status = tk.Label(self, text="", bg=C["panel"], fg=C["muted"], anchor="w", font=FONT["small"], padx=10)
        self.status.pack(fill="x", side="bottom")

    def _view_bar(self, parent):
        """Alterna entre blocos e previa, e da acesso ao mapa e as telas prontas."""
        bar = tk.Frame(parent, bg=C["bg"])
        bar.pack(fill="x", padx=8, pady=(0, 4))
        self.view_mode = tk.StringVar(value="blocks")
        for value, text in (("blocks", "Blocos"), ("preview", "Prévia")):
            tk.Radiobutton(bar, text=text, value=value, variable=self.view_mode, indicatoron=False,
                           command=self.set_view_mode, bg=C["panel2"], fg=C["text"], selectcolor=C["accent_dark"],
                           activebackground=C["card_hover"], activeforeground=C["text"], bd=0, padx=12, pady=3,
                           font=FONT["small"], relief="flat", highlightthickness=0).pack(side="left", padx=(0, 1))
        library = ttk.Button(bar, text="Telas prontas", style="Tool.TButton", command=self.app.open_screen_library)
        library.pack(side="right")
        Tooltip(library, "Inserir telas prontas: login, vitrine, planos, FAQ, contato...")
        nav_map = ttk.Button(bar, text="Mapa de navegação", style="Tool.TButton", command=self.app.open_navigation_map)
        nav_map.pack(side="right", padx=4)
        Tooltip(nav_map, "Ver como as telas se ligam (Ctrl+M)")

    def set_view_mode(self):
        self.canvas.preview = self.view_mode.get() == "preview"
        self.canvas.redraw()

    def _toolbar(self):
        header = tk.Frame(self, bg=C["panel"])
        header.pack(fill="x")
        bar = tk.Frame(header, bg=C["panel"])
        bar.pack(fill="x")
        logo = tk.Canvas(bar, width=28, height=28, bg=C["panel"], highlightthickness=0)
        logo.create_rectangle(2, 2, 26, 26, fill=C["accent"], outline="")
        for x0, y0, x1, y1 in ((7, 17, 21, 21), (9, 12, 19, 15), (11, 7, 17, 10)):
            logo.create_rectangle(x0, y0, x1, y1, fill="#FFFFFF", outline="")
        logo.pack(side="left", padx=(10, 6), pady=6)
        self.title_label = tk.Label(bar, text=APP_NAME, bg=C["panel"], fg=C["text"], font=FONT["h2"])
        self.title_label.pack(side="left")
        self.subtitle_label = tk.Label(bar, text="", bg=C["panel"], fg=C["muted"], font=FONT["small"])
        self.subtitle_label.pack(side="left", padx=10)
        app = self.app
        gen = ttk.Button(bar, text="Gerar projeto", style="Accent.TButton", command=app.generate_dialog)
        gen.pack(side="right", padx=8, pady=6)
        Tooltip(gen, "Gera a pasta do projeto para o Android Studio (Ctrl+G)")
        right = tk.Frame(header, bg=C["panel"])
        right.pack(fill="x", padx=6, pady=(0, 4))
        items = [
            ("Novo", app.new_project, "Novo projeto (Ctrl+N)"),
            ("Abrir", app.open_project, "Abrir projeto .dbp (Ctrl+O)"),
            ("Salvar", app.save, "Salvar projeto (Ctrl+S)"),
            (None, None, None),
            ("Desfazer", app.undo, "Desfazer (Ctrl+Z)"),
            ("Refazer", app.redo, "Refazer (Ctrl+Y)"),
            (None, None, None),
            ("Modelos", app.open_template_gallery, "Galeria com os modelos de aplicativos"),
            ("APIs", app.edit_apis, "Cadastrar APIs REST, endpoints e modelos"),
            ("Banco", app.edit_database, "Entidades do banco local (Room)"),
            ("Projeto", app.edit_project_settings, "Nome, pacote, interface, cores, SDK e navegação"),
            (None, None, None),
            ("Organizar", app.organize, "Corrige referências, cria telas faltantes e integra tudo"),
            ("Código", app.preview_code, "Pré-visualizar todos os arquivos gerados"),
        ]
        for text, command, tip in items:
            if text is None:
                tk.Frame(right, bg=C["border"], width=1, height=22).pack(side="left", padx=4)
                continue
            button = ttk.Button(right, text=text, style="Tool.TButton", command=command, width=len(text) + 1)
            button.pack(side="left")
            Tooltip(button, tip)
        more = ttk.Menubutton(right, text="Mais", style="Tool.TButton", width=6)
        menu = tk.Menu(more, tearoff=0)
        menu.add_command(label="Salvar como...", command=app.save_as)
        menu.add_command(label="Validar projeto (F5)", command=app.validate)
        menu.add_separator()
        menu.add_command(label="Configurações e versões...", command=app.edit_app_settings)
        menu.add_command(label="Sobre o DroidBlocks", command=lambda: AboutDialog(app.root).show())
        more["menu"] = menu
        more.pack(side="left")

    # ------------------------------------------------------------ atualizacoes

    def refresh_screens(self):
        bar = self.screen_bar
        for child in bar.winfo_children():
            child.destroy()
        project = self.app.project
        current = self.app.current_screen()
        start = project.get_start_screen()
        for screen in project.screens:
            active = screen is current
            label = (screen.title or screen.name) + ("  (inicial)" if screen is start else "")
            btn = tk.Label(bar, text=label, bg=C["accent"] if active else C["card"],
                           fg="#FFFFFF" if active else C["muted"], padx=10, pady=4, cursor="hand2", font=FONT["small"])
            btn.bind("<Button-1>", lambda e, s=screen: self.app.select_screen(s.id))
        add = ttk.Button(bar, text="+ Tela", style="Tool.TButton", command=self.app.add_screen, width=7)
        Tooltip(add, "Adicionar uma nova tela")
        self.reflow_screens()

    def reflow_screens(self, _event=None):
        """Distribui as abas de telas em varias linhas quando nao cabem em uma."""
        bar = self.screen_bar
        width = max(bar.winfo_width(), 200)
        x = y = 0
        row_h = 0
        for child in bar.winfo_children():
            w, h = child.winfo_reqwidth(), child.winfo_reqheight()
            if x and x + w > width:
                x = 0
                y += row_h + 3
                row_h = 0
            child.place(x=x, y=y)
            x += w + 3
            row_h = max(row_h, h)
        bar.configure(height=y + row_h + 2)

    def show_diagnostics(self, resolved):
        self.diag_tree.delete(*self.diag_tree.get_children())
        order = {"erro": 0, "aviso": 1, "info": 2}
        for level, message in sorted(resolved.diagnostics, key=lambda d: order.get(d[0], 3)):
            self.diag_tree.insert("", "end", values=(level, t(message)), tags=(level,))
        errors = sum(1 for d in resolved.diagnostics if d[0] == "erro")
        warnings = sum(1 for d in resolved.diagnostics if d[0] == "aviso")
        title = "Diagnóstico"
        if errors or warnings:
            title += f" ({errors} erros, {warnings} avisos)"
        self.bottom.tab(0, text=title)

    def show_code(self, files):
        self.code_cache = files
        screen = self.app.current_screen()
        current = self.code_file.get()
        names = list(files)
        self.code_file.configure(values=names)
        if current not in files:
            preferred = [n for n in names if screen and f"/{to_pascal(screen.name)}" in n]
            current = preferred[0] if preferred else (names[0] if names else "")
        self.code_file.set(current)
        self.show_code_file()

    def show_code_file(self):
        name = self.code_file.get()
        content = self.code_cache.get(name, "")
        self.code_text.configure(state="normal")
        self.code_text.delete("1.0", "end")
        self.code_text.insert("1.0", content if isinstance(content, str) else "[binário]")
        if name.endswith(".kt"):
            highlight(self.code_text)
        self.code_text.configure(state="disabled")


class App:
    """Estado da aplicacao: projeto aberto, selecao, historico e acoes."""

    def __init__(self, root):
        self.root = root
        self.settings = Settings()
        self.project = None
        self.path = None
        self.dirty = False
        self.history = []
        self.future = []
        self.current_screen_id = None
        self.selected_id = None
        self.clipboard = None
        self._jobs = {}
        self._resolved = None
        theme.setup(root)
        root.title(APP_NAME)
        root.geometry("1440x880")
        root.minsize(1100, 700)
        self._set_icon()
        self.editor = None
        self.welcome = WelcomeFrame(root, self)
        self.welcome.pack(fill="both", expand=True)
        root.protocol("WM_DELETE_WINDOW", self.quit)
        self._bind_keys()

    def _set_icon(self):
        try:
            self._icon = tk.PhotoImage(data=render_icon(64, C["accent"]))
            self.root.iconphoto(True, self._icon)
        except tk.TclError:
            pass

    def _bind_keys(self):
        r = self.root
        mod = "Command" if r.tk.call("tk", "windowingsystem") == "aqua" else "Control"
        bindings = {
            f"<{mod}-n>": lambda e: self.new_project(), f"<{mod}-o>": lambda e: self.open_project(),
            f"<{mod}-s>": lambda e: self.save(), f"<{mod}-S>": lambda e: self.save_as(),
            f"<{mod}-z>": lambda e: self.undo(), f"<{mod}-y>": lambda e: self.redo(),
            f"<{mod}-Z>": lambda e: self.redo(), f"<{mod}-g>": lambda e: self.generate_dialog(),
            "<F5>": lambda e: self.validate(),
        }
        for seq, fn in bindings.items():
            r.bind_all(seq, fn)
        r.bind_all(f"<{mod}-d>", lambda e: self._if_canvas(self.duplicate_selected))
        r.bind_all(f"<{mod}-c>", lambda e: self._if_canvas(self.copy_selected), add="+")
        r.bind_all(f"<{mod}-v>", lambda e: self._if_canvas(self.paste_block), add="+")
        r.bind_all("<Delete>", lambda e: self._if_canvas(self.delete_selected))
        r.bind_all("<Up>", lambda e: self._if_canvas(lambda: self.select_relative(-1)))
        r.bind_all("<Down>", lambda e: self._if_canvas(lambda: self.select_relative(1)))
        r.bind_all("<Alt-Up>", lambda e: self._if_canvas(lambda: self.shift_selected(-1)))
        r.bind_all("<Alt-Down>", lambda e: self._if_canvas(lambda: self.shift_selected(1)))
        r.bind_all(f"<{mod}-m>", lambda e: self.open_navigation_map() if self.editor else None)
        r.bind_all(f"<{mod}-p>", lambda e: self.toggle_preview() if self.editor else None)

    def _if_canvas(self, fn):
        """Executa atalhos de blocos apenas quando o foco nao esta em um campo de texto."""
        try:
            focus = self.root.focus_get()
        except (KeyError, tk.TclError):
            focus = None
        if isinstance(focus, (tk.Entry, ttk.Entry, tk.Text, ttk.Combobox, ttk.Treeview, tk.Listbox, ttk.Spinbox)):
            return
        if self.editor:
            fn()

    # ------------------------------------------------------------ projeto

    def load_project(self, project, path):
        self.project = project
        self.path = Path(path) if path else None
        self.history, self.future = [], []
        self.dirty = path is None
        start = project.get_start_screen()
        self.current_screen_id = start.id if start else None
        self.selected_id = None
        if self.welcome:
            self.welcome.destroy()
            self.welcome = None
        if self.editor is None:
            self.editor = EditorFrame(self.root, self)
            self.editor.pack(fill="both", expand=True)
        self.refresh_all()
        self.log(f"Projeto '{project.name}' aberto.")

    def new_project(self):
        if not self.confirm_discard():
            return
        if self.editor:
            self.editor.destroy()
            self.editor = None
        self.project = None
        self.welcome = WelcomeFrame(self.root, self)
        self.welcome.pack(fill="both", expand=True)
        self.root.title(APP_NAME)

    def open_project(self, path=None):
        if not self.confirm_discard():
            return
        if path is None:
            path = filedialog.askopenfilename(filetypes=[("Projeto DroidBlocks", f"*{PROJECT_EXT}"), ("Todos", "*.*")])
            if not path:
                return
        try:
            project = load_project(path)
        except Exception as exc:
            messagebox.showerror("Erro ao abrir", f"Não foi possível abrir o projeto:\n{exc}")
            return
        self.settings.add_recent(path)
        self.load_project(project, path)

    def save(self):
        if self.project is None:
            return
        if self.path is None:
            return self.save_as()
        save_project(self.project, self.path)
        self.dirty = False
        self.settings.add_recent(self.path)
        self.update_title()
        self.log(f"Projeto salvo em {self.path}")

    def save_as(self):
        if self.project is None:
            return
        folder = Path(self.settings["output_dir"]).expanduser()
        path = filedialog.asksaveasfilename(defaultextension=PROJECT_EXT, initialdir=str(folder),
                                            initialfile=to_pascal(self.project.name) + PROJECT_EXT,
                                            filetypes=[("Projeto DroidBlocks", f"*{PROJECT_EXT}")])
        if path:
            self.path = Path(path)
            self.save()

    def confirm_discard(self):
        if self.project is None or not self.dirty:
            return True
        answer = messagebox.askyesnocancel("Alterações não salvas", "Salvar o projeto atual antes de continuar?")
        if answer is None:
            return False
        if answer:
            self.save()
            return not self.dirty
        return True

    def quit(self):
        if self.confirm_discard():
            self.root.destroy()

    # ------------------------------------------------------------ historico

    def snapshot(self):
        return json.dumps(self.project.to_dict())

    def push_history(self):
        if self.project is None:
            return
        snap = self.snapshot()
        if self.history and self.history[-1] == snap:
            return
        self.history.append(snap)
        self.history = self.history[-80:]
        self.future.clear()

    def _restore(self, snap):
        self.project = Project.from_dict(json.loads(snap))
        if not self.project.screen_by_id(self.current_screen_id):
            start = self.project.get_start_screen()
            self.current_screen_id = start.id if start else None
        if self.selected_component() is None:
            self.selected_id = None
        self.dirty = True
        self.refresh_all()

    def undo(self):
        if self.project and self.history:
            self.future.append(self.snapshot())
            self._restore(self.history.pop())
            self.log("Desfeito.")

    def redo(self):
        if self.project and self.future:
            self.history.append(self.snapshot())
            self._restore(self.future.pop())
            self.log("Refeito.")

    # ------------------------------------------------------------ atualizacao da interface

    def changed(self, history=True, rebuild_props=False, screens=False):
        """Chamado apos qualquer alteracao no projeto."""
        self.dirty = True
        self._resolved = None
        if self.editor:
            self.editor.canvas.redraw()
            if screens:
                self.editor.refresh_screens()
            if rebuild_props:
                self.editor.properties.show()
        self.update_title()
        self.debounce("diag", 400, self.validate)
        self.debounce("code", 900, self.refresh_code)
        self.debounce("palette", 500, self.refresh_catalogs)
        if self.settings["autosave"] and self.path:
            self.debounce("save", 1500, self.save)

    def before_change(self, coalesce_key=None):
        """Registra o estado anterior para desfazer (agrupando digitacao continua)."""
        if coalesce_key and self._jobs.get("hist_key") == coalesce_key:
            return
        self._jobs["hist_key"] = coalesce_key
        self.push_history()

    def debounce(self, name, delay, fn):
        job = self._jobs.get(name)
        if job:
            self.root.after_cancel(job)
        self._jobs[name] = self.root.after(delay, fn)

    def refresh_all(self):
        if not self.editor:
            return
        self.editor.refresh_screens()
        self.editor.canvas.redraw()
        self.editor.properties.show()
        self.refresh_catalogs()
        self.validate()
        self.refresh_code()
        self.update_title()

    def refresh_catalogs(self):
        if self.editor:
            self.editor.features.refresh()
            self.editor.algorithms.refresh()

    def update_title(self):
        if not self.project:
            return
        mark = " *" if self.dirty else ""
        where = f" - {self.path.name}" if self.path else ""
        self.root.title(f"{self.project.name}{mark}{where} - {APP_NAME}")
        if self.editor:
            ui = "Jetpack Compose" if self.project.ui_mode == "compose" else "XML Views"
            self.editor.title_label.configure(text=self.project.name + mark)
            self.editor.subtitle_label.configure(text=f"{self.project.package}  |  {ui}  |  {len(self.project.screens)} telas")
            r = self.resolved()
            self.editor.status.configure(
                text=f"{len(r.features)} funcionalidades ativas  |  {len(r.libs)} bibliotecas  |  "
                     f"{len(r.permissions)} permissões  |  {len(self.project.entities)} entidades  |  "
                     f"{len(self.project.apis)} APIs  |  {len(r.algorithms)} algoritmos")

    def resolved(self):
        if self._resolved is None and self.project:
            self._resolved = resolve(self.project)
        return self._resolved

    def resolved_keys(self):
        r = self.resolved()
        return r.feature_keys if r else set()

    def validate(self):
        if self.editor and self.project:
            self._resolved = None
            self.editor.show_diagnostics(self.resolved())
            self.update_title()

    def refresh_code(self):
        if not (self.editor and self.project):
            return
        screen = self.current_screen()
        try:
            result = generate(self.project, self.settings["versions"] or {}, preview=True)
        except Exception as exc:
            self.log(f"Falha ao gerar a pré-visualização: {exc}")
            return
        files = {}
        if screen:
            key = to_pascal(screen.name)
            for path, content in result.files.items():
                name = path.rsplit("/", 1)[-1]
                if name.startswith(key) or name == f"activity_{screen.name.lower()}.xml":
                    files[path] = content
        for extra in ("gradle/libs.versions.toml", "app/build.gradle.kts", "app/src/main/AndroidManifest.xml"):
            if extra in result.files:
                files[extra] = result.files[extra]
        self.editor.show_code(files)

    def log(self, message):
        if self.editor:
            box = self.editor.log_text
            box.configure(state="normal")
            box.insert("end", message + "\n")
            box.see("end")
            box.configure(state="disabled")

    # ------------------------------------------------------------ telas

    def current_screen(self):
        return self.project.screen_by_id(self.current_screen_id) if self.project else None

    def select_screen(self, sid, focus=False):
        self.current_screen_id = sid
        self.selected_id = None
        self.editor.refresh_screens()
        self.editor.canvas.redraw()
        self.editor.properties.show()
        self.refresh_code()

    def add_screen(self):
        before = {s.name for s in self.project.screens}
        index = len(self.project.screens) + 1
        name = f"Tela{index}"
        while name in before:
            index += 1
            name = f"Tela{index}"
        self.before_change()
        screen = Screen(name=name, title=f"Tela {index}", components=[
            Component("title", dict(default_props("title"), text=f"Tela {index}"), new_id())])
        self.project.screens.append(screen)
        self.current_screen_id = screen.id
        self.selected_id = None
        self.changed(screens=True, rebuild_props=True)

    def duplicate_screen(self):
        screen = self.current_screen()
        if not screen:
            return
        self.before_change()
        copy_screen = copy.deepcopy(screen)
        copy_screen.id = new_id("s")
        base = screen.name + "Copia"
        name, n = base, 2
        while self.project.screen_by_name(name):
            name, n = f"{base}{n}", n + 1
        copy_screen.name = name
        copy_screen.title = (screen.title or screen.name) + " (cópia)"
        for comp in copy_screen.components:
            comp.id = new_id()
        self.project.screens.insert(self.project.screens.index(screen) + 1, copy_screen)
        self.current_screen_id = copy_screen.id
        self.changed(screens=True, rebuild_props=True)

    def delete_screen(self):
        screen = self.current_screen()
        if not screen or not messagebox.askyesno("Excluir tela", f"Excluir a tela '{screen.title or screen.name}'?"):
            return
        self.before_change()
        index = self.project.screens.index(screen)
        self.project.screens.remove(screen)
        if self.project.start_screen == screen.name:
            self.project.start_screen = self.project.screens[0].name if self.project.screens else ""
        if self.project.screens:
            self.current_screen_id = self.project.screens[max(0, index - 1)].id
        else:
            self.current_screen_id = None
        self.selected_id = None
        self.changed(screens=True, rebuild_props=True)

    def rename_screen(self, screen, new_name):
        name = to_pascal(new_name, "Tela")
        if name == screen.name:
            return
        if self.project.screen_by_name(name):
            messagebox.showerror("Nome em uso", f"Já existe uma tela chamada {name}.")
            return
        self.before_change()
        old = screen.name
        screen.name = name
        if self.project.start_screen == old:
            self.project.start_screen = name
        # Atualiza acoes que apontavam para o nome antigo.
        for s in self.project.screens:
            for comp in s.components:
                for key, value in comp.props.items():
                    if isinstance(value, str) and ":" in value and value.split(":", 1)[1] == old:
                        comp.props[key] = value.split(":", 1)[0] + ":" + name
        self.changed(screens=True, rebuild_props=True)
        self.log(f"Tela {old} renomeada para {name}; ações atualizadas.")

    def update_screen(self, screen, attr, value):
        self.before_change(f"screen:{screen.id}:{attr}")
        setattr(screen, attr, value)
        self.changed(screens=attr in ("title", "in_nav"))

    def set_start_screen(self, screen):
        self.before_change()
        self.project.start_screen = screen.name
        self.changed(screens=True, rebuild_props=True)

    # ------------------------------------------------------------ blocos

    def selected_component(self):
        screen = self.current_screen()
        if not screen or not self.selected_id:
            return None
        return next((c for c in screen.components if c.id == self.selected_id), None)

    def select_component(self, cid):
        if cid == self.selected_id:
            return
        self.selected_id = cid
        self._jobs["hist_key"] = None
        self.editor.canvas.redraw()
        self.editor.properties.show()

    def focus_properties(self):
        widget = self.editor.properties.first_widget
        if widget:
            widget.focus_set()

    def add_component(self, ctype, index=None):
        screen = self.current_screen()
        if screen is None:
            self.add_screen()
            screen = self.current_screen()
        self.before_change()
        comp = Component(ctype, default_props(ctype), new_id())
        if ctype in ("text_field", "checkbox", "switch", "slider", "radio_group", "dropdown", "chips", "tabs",
                     "date_picker", "rating", "stepper", "calendar"):
            used = {c.props.get("key") for c in screen.components}
            base = comp.props.get("key", "field")
            key, n = base, 2
            while key in used:
                key, n = f"{base}{n}", n + 1
            comp.props["key"] = key
        if index is None or index > len(screen.components):
            screen.components.append(comp)
        else:
            screen.components.insert(index, comp)
        self.selected_id = comp.id
        self.changed(rebuild_props=True)
        spec = COMPONENTS[ctype]
        if spec.requires:
            self.log(f"Bloco {t(spec.label)} adicionado (ativa automaticamente: {', '.join(spec.requires)}).")

    def move_component(self, cid, index):
        screen = self.current_screen()
        comp = next((c for c in screen.components if c.id == cid), None)
        if comp is None:
            return
        old = screen.components.index(comp)
        if index > old:
            index -= 1
        if index == old:
            return
        self.before_change()
        screen.components.remove(comp)
        screen.components.insert(index, comp)
        self.changed()

    def select_relative(self, delta):
        """Seleciona o bloco anterior ou seguinte na tela atual (setas do teclado)."""
        screen = self.current_screen()
        if not screen or not screen.components:
            return
        ids = [c.id for c in screen.components]
        if self.selected_id in ids:
            index = max(0, min(len(ids) - 1, ids.index(self.selected_id) + delta))
        else:
            index = 0 if delta > 0 else len(ids) - 1
        self.select_component(ids[index])

    def toggle_preview(self):
        mode = self.editor.view_mode
        mode.set("blocks" if mode.get() == "preview" else "preview")
        self.editor.set_view_mode()

    def open_navigation_map(self):
        NavigationMap(self.root, self).show()

    def open_screen_library(self):
        ScreenLibrary(self.root, self).show()

    def shift_selected(self, delta):
        screen = self.current_screen()
        comp = self.selected_component()
        if not comp:
            return
        index = screen.components.index(comp)
        target = max(0, min(len(screen.components) - 1, index + delta))
        if target != index:
            self.before_change()
            screen.components.insert(target, screen.components.pop(index))
            self.changed()

    def duplicate_selected(self):
        screen = self.current_screen()
        comp = self.selected_component()
        if not comp:
            return
        self.before_change()
        clone = Component(comp.type, copy.deepcopy(comp.props), new_id())
        screen.components.insert(screen.components.index(comp) + 1, clone)
        self.selected_id = clone.id
        self.changed(rebuild_props=True)

    def delete_selected(self):
        screen = self.current_screen()
        comp = self.selected_component()
        if not comp:
            return
        self.before_change()
        index = screen.components.index(comp)
        screen.components.remove(comp)
        self.selected_id = screen.components[min(index, len(screen.components) - 1)].id if screen.components else None
        self.changed(rebuild_props=True)

    def copy_selected(self):
        comp = self.selected_component()
        if comp:
            self.clipboard = (comp.type, copy.deepcopy(comp.props))
            self.log("Bloco copiado.")

    def paste_block(self):
        if not self.clipboard:
            return
        screen = self.current_screen()
        self.before_change()
        ctype, props = self.clipboard
        comp = Component(ctype, copy.deepcopy(props), new_id())
        selected = self.selected_component()
        index = screen.components.index(selected) + 1 if selected else len(screen.components)
        screen.components.insert(index, comp)
        self.selected_id = comp.id
        self.changed(rebuild_props=True)

    def update_prop(self, comp, key, value):
        if comp.props.get(key) == value:
            return
        self.before_change(f"prop:{comp.id}:{key}")
        comp.props[key] = value
        self.changed()

    # ------------------------------------------------------------ funcionalidades e algoritmos

    def toggle_feature(self, key):
        self.before_change()
        if key in self.project.features:
            self.project.features.remove(key)
            needed_by = key in self.resolved_keys() and key not in self.project.features
            self.log(f"Funcionalidade removida: {key}" + (" (continua ativa por dependência)" if needed_by else ""))
        else:
            self.project.features.append(key)
            self.log(f"Funcionalidade ativada: {key}")
        self.changed()
        self._resolved = None
        self.refresh_catalogs()

    def toggle_algorithm(self, key):
        self.before_change()
        if key in self.project.algorithms:
            self.project.algorithms.remove(key)
        else:
            self.project.algorithms.append(key)
        self.changed()
        self.refresh_catalogs()

    # ------------------------------------------------------------ dialogos

    def open_template_gallery(self):
        result = TemplateGallery(self.root).show()
        if not result:
            return
        if self.project is not None:
            answer = messagebox.askyesnocancel(
                "Usar modelo", "Substituir o projeto atual por este modelo?\n\n"
                               "Sim: substitui mantendo nome e pacote.\nNão: adiciona as telas do modelo ao projeto atual.")
            if answer is None:
                return
            self.before_change()
            built = template_catalog.build_project(result, self.project.name, self.project.package)
            if answer:
                built.ui_mode = self.project.ui_mode
                self.project = built
                start = built.get_start_screen()
                self.current_screen_id = start.id if start else None
            else:
                existing = {s.name for s in self.project.screens}
                for screen in built.screens:
                    if screen.name in existing:
                        screen.name = screen.name + "2"
                    self.project.screens.append(screen)
                self.project.features = list(dict.fromkeys(self.project.features + built.features))
                self.project.entities += [e for e in built.entities if not self.project.entity_by_name(e.name)]
                self.project.apis += [a for a in built.apis if not self.project.api_by_name(a.name)]
                for k, v in built.samples.items():
                    self.project.samples.setdefault(k, v)
            self.selected_id = None
            self.changed(screens=True, rebuild_props=True)
            self.log(f"Modelo aplicado: {result['name']}")
        else:
            project = template_catalog.build_project(result)
            self.load_project(project, None)

    def edit_apis(self):
        result = ApiEditor(self.root, self.project).show()
        if result is not None:
            self.before_change()
            self.project.apis = result
            self.changed(rebuild_props=True)
            self.log(f"{len(result)} APIs configuradas.")

    def edit_database(self):
        result = DatabaseEditor(self.root, self.project).show()
        if result is None:
            return
        entities, crud = result
        self.before_change()
        self.project.entities = entities
        for name in crud:
            entity = self.project.entity_by_name(name)
            if entity:
                for screen in crud_screens(entity):
                    if not self.project.screen_by_name(screen.name):
                        self.project.screens.append(screen)
                self.log(f"Telas de lista e cadastro criadas para {name}.")
        self.changed(screens=True, rebuild_props=True)

    def edit_project_settings(self):
        result = ProjectSettings(self.root, self.project).show()
        if result:
            self.before_change()
            for key, value in result.items():
                setattr(self.project, key, value)
            self.changed(screens=True, rebuild_props=True)

    def edit_app_settings(self):
        if AppSettings(self.root, self.settings).show():
            self.refresh_code()

    def organize(self):
        self.before_change()
        changes = auto_organize(self.project)
        start = self.project.get_start_screen()
        if not self.project.screen_by_id(self.current_screen_id) and start:
            self.current_screen_id = start.id
        self.changed(screens=True, rebuild_props=True)
        for change in changes:
            self.log(t(change))
        messagebox.showinfo("Organização automática", "\n".join(t(c) for c in changes[:20]))

    def preview_code(self):
        try:
            result = generate(self.project, self.settings["versions"] or {}, preview=True)
        except Exception as exc:
            messagebox.showerror("Erro", str(exc))
            return
        screen = self.current_screen()
        focus = None
        if screen:
            focus = next((p for p in result.files if p.endswith(f"/{to_pascal(screen.name)}Screen.kt")
                          or p.endswith(f"/{to_pascal(screen.name)}Activity.kt")), None)
        CodePreview(self.root, result, focus).show()

    def generate_dialog(self):
        if self.project:
            GenerateDialog(self.root, self).show()


def run():
    root = tk.Tk()
    App(root)
    root.mainloop()
