"""Tema visual (tons de preto e azul) e widgets auxiliares da interface."""

import sys
import tkinter as tk
from tkinter import ttk
import tkinter.font as tkfont

C = {
    "bg": "#0A0E14",
    "panel": "#0F1621",
    "panel2": "#131C2A",
    "card": "#172235",
    "card_hover": "#1C2B42",
    "border": "#24344D",
    "accent": "#2F81F7",
    "accent_hover": "#4C94FF",
    "accent_dark": "#1B4F99",
    "select": "#1D3B66",
    "text": "#E6EDF3",
    "muted": "#8B9BB4",
    "dim": "#5C6B82",
    "success": "#3FB950",
    "warning": "#D29922",
    "error": "#F85149",
    "phone": "#05080D",
    "phone_screen": "#0E1520",
}

# Cores dos blocos por categoria (familia de azuis).
BLOCK_COLORS = {
    "Basicos": "#2F81F7",
    "Entrada de dados": "#3B5BDB",
    "Listas e dados": "#0B7FAB",
    "Midia e mapas": "#5B6EE1",
    "Layout": "#4A6283",
}

FONT = {}


def _family(candidates, fallback):
    available = set(tkfont.families())
    for name in candidates:
        if name in available:
            return name
    return fallback


def setup(root):
    """Configura fontes e estilos ttk do aplicativo inteiro."""
    default = tkfont.nametofont("TkDefaultFont")
    if sys.platform.startswith("win"):
        family = _family(["Segoe UI"], default.actual("family"))
        mono = _family(["Cascadia Mono", "Consolas"], "Courier New")
    elif sys.platform == "darwin":
        family = _family(["SF Pro Text", "Helvetica Neue", "Helvetica"], default.actual("family"))
        mono = _family(["SF Mono", "Menlo", "Monaco"], "Courier")
    else:
        family = _family(["Inter", "Ubuntu", "Cantarell", "Noto Sans", "DejaVu Sans", "Liberation Sans"],
                         default.actual("family"))
        mono = _family(["JetBrains Mono", "Ubuntu Mono", "DejaVu Sans Mono", "Liberation Mono"], "Courier")
    FONT.update({
        "base": (family, 10), "small": (family, 9), "bold": (family, 10, "bold"),
        "title": (family, 15, "bold"), "h2": (family, 12, "bold"), "big": (family, 22, "bold"),
        "mono": (mono, 10), "block": (family, 10, "bold"), "block_small": (family, 9),
    })
    for name in ("TkDefaultFont", "TkTextFont", "TkMenuFont", "TkHeadingFont"):
        try:
            tkfont.nametofont(name).configure(family=family, size=10)
        except tk.TclError:
            pass

    root.configure(bg=C["bg"])
    root.option_add("*TCombobox*Listbox.background", C["panel2"])
    root.option_add("*TCombobox*Listbox.foreground", C["text"])
    root.option_add("*TCombobox*Listbox.selectBackground", C["accent"])
    root.option_add("*TCombobox*Listbox.selectForeground", "#FFFFFF")
    root.option_add("*TCombobox*Listbox.font", FONT["base"])
    root.option_add("*Menu.background", C["panel2"])
    root.option_add("*Menu.foreground", C["text"])
    root.option_add("*Menu.activeBackground", C["accent"])
    root.option_add("*Menu.activeForeground", "#FFFFFF")
    root.option_add("*Menu.relief", "flat")

    style = ttk.Style(root)
    style.theme_use("clam")
    style.configure(".", background=C["panel"], foreground=C["text"], fieldbackground=C["panel2"],
                    bordercolor=C["border"], lightcolor=C["panel"], darkcolor=C["panel"],
                    troughcolor=C["bg"], focuscolor=C["accent"], selectbackground=C["accent"],
                    selectforeground="#FFFFFF", insertcolor=C["text"], font=FONT["base"])
    style.configure("TFrame", background=C["panel"])
    style.configure("Bg.TFrame", background=C["bg"])
    style.configure("Card.TFrame", background=C["card"])
    style.configure("Panel2.TFrame", background=C["panel2"])
    style.configure("TLabel", background=C["panel"], foreground=C["text"])
    style.configure("Bg.TLabel", background=C["bg"])
    style.configure("Card.TLabel", background=C["card"])
    style.configure("Panel2.TLabel", background=C["panel2"])
    style.configure("Muted.TLabel", foreground=C["muted"])
    style.configure("MutedBg.TLabel", background=C["bg"], foreground=C["muted"])
    style.configure("MutedCard.TLabel", background=C["card"], foreground=C["muted"])
    style.configure("Title.TLabel", font=FONT["title"])
    style.configure("TitleBg.TLabel", font=FONT["title"], background=C["bg"])
    style.configure("Big.TLabel", font=FONT["big"], background=C["bg"], foreground=C["text"])
    style.configure("H2.TLabel", font=FONT["h2"])
    style.configure("H2Card.TLabel", font=FONT["h2"], background=C["card"])
    style.configure("Accent.TLabel", foreground=C["accent_hover"])
    style.configure("Error.TLabel", foreground=C["error"])

    style.configure("TButton", background=C["card"], foreground=C["text"], bordercolor=C["border"],
                    lightcolor=C["card"], darkcolor=C["card"], padding=(10, 5), relief="flat")
    style.map("TButton", background=[("pressed", C["select"]), ("active", C["card_hover"]),
                                     ("disabled", C["panel"])],
              foreground=[("disabled", C["dim"])], bordercolor=[("active", C["accent"])])
    style.configure("Accent.TButton", background=C["accent"], foreground="#FFFFFF",
                    bordercolor=C["accent"], lightcolor=C["accent"], darkcolor=C["accent"],
                    font=FONT["bold"], padding=(14, 6))
    style.map("Accent.TButton", background=[("pressed", C["accent_dark"]), ("active", C["accent_hover"])])
    style.configure("Tool.TButton", background=C["panel"], bordercolor=C["panel"], padding=(8, 4))
    style.map("Tool.TButton", background=[("active", C["card_hover"])], bordercolor=[("active", C["border"])])
    style.configure("Link.TButton", background=C["bg"], bordercolor=C["bg"], foreground=C["accent_hover"],
                    padding=(4, 2))
    style.map("Link.TButton", background=[("active", C["bg"])], foreground=[("active", "#FFFFFF")])
    style.configure("Danger.TButton", foreground=C["error"])

    for widget in ("TEntry", "TCombobox", "TSpinbox"):
        style.configure(widget, fieldbackground=C["panel2"], foreground=C["text"], bordercolor=C["border"],
                        lightcolor=C["panel2"], darkcolor=C["panel2"], arrowcolor=C["muted"],
                        padding=4, insertcolor=C["text"])
        style.map(widget, bordercolor=[("focus", C["accent"])], lightcolor=[("focus", C["accent"])],
                  fieldbackground=[("readonly", C["panel2"]), ("disabled", C["panel"])],
                  foreground=[("disabled", C["dim"])], selectbackground=[("readonly", C["panel2"])],
                  selectforeground=[("readonly", C["text"])])
    style.configure("TCheckbutton", background=C["panel"], foreground=C["text"], indicatorbackground=C["panel2"],
                    indicatorforeground=C["accent"])
    style.map("TCheckbutton", background=[("active", C["panel"])],
              indicatorbackground=[("selected", C["accent"]), ("active", C["card"])],
              indicatorforeground=[("selected", "#FFFFFF")])
    style.configure("Card.TCheckbutton", background=C["card"])
    style.map("Card.TCheckbutton", background=[("active", C["card"])])
    style.configure("TRadiobutton", background=C["panel"], foreground=C["text"], indicatorbackground=C["panel2"])
    style.map("TRadiobutton", background=[("active", C["panel"])],
              indicatorbackground=[("selected", C["accent"]), ("active", C["card"])])
    style.configure("Card.TRadiobutton", background=C["card"])
    style.map("Card.TRadiobutton", background=[("active", C["card"])])

    style.configure("TNotebook", background=C["panel"], bordercolor=C["border"], tabmargins=(4, 4, 4, 0))
    style.configure("TNotebook.Tab", background=C["panel"], foreground=C["muted"], padding=(12, 5),
                    bordercolor=C["border"], lightcolor=C["panel"])
    style.map("TNotebook.Tab", background=[("selected", C["panel2"]), ("active", C["card"])],
              foreground=[("selected", C["text"]), ("active", C["text"])],
              lightcolor=[("selected", C["accent"])])

    style.configure("Treeview", background=C["panel2"], fieldbackground=C["panel2"], foreground=C["text"],
                    bordercolor=C["border"], rowheight=24)
    style.map("Treeview", background=[("selected", C["select"])], foreground=[("selected", "#FFFFFF")])
    style.configure("Treeview.Heading", background=C["card"], foreground=C["muted"], bordercolor=C["border"],
                    relief="flat", font=FONT["small"])
    style.map("Treeview.Heading", background=[("active", C["card_hover"])])

    for orient in ("Vertical", "Horizontal"):
        style.configure(f"{orient}.TScrollbar", background=C["card"], troughcolor=C["panel"],
                        bordercolor=C["panel"], arrowcolor=C["muted"], lightcolor=C["card"], darkcolor=C["card"])
        style.map(f"{orient}.TScrollbar", background=[("active", C["accent_dark"])])
    style.configure("TPanedwindow", background=C["bg"])
    style.configure("Sash", sashthickness=5, gripcount=0, background=C["bg"])
    style.configure("TLabelframe", background=C["panel"], bordercolor=C["border"])
    style.configure("TLabelframe.Label", background=C["panel"], foreground=C["muted"], font=FONT["small"])
    style.configure("TSeparator", background=C["border"])
    style.configure("Horizontal.TProgressbar", background=C["accent"], troughcolor=C["panel2"],
                    bordercolor=C["border"], lightcolor=C["accent"], darkcolor=C["accent"])
    return style


class ScrollFrame(ttk.Frame):
    """Frame com rolagem vertical. Adicione widgets em .body."""

    def __init__(self, master, bg=None, **kwargs):
        super().__init__(master, **kwargs)
        bg = bg or C["panel"]
        self.canvas = tk.Canvas(self, bg=bg, highlightthickness=0, bd=0)
        self.scroll = ttk.Scrollbar(self, orient="vertical", command=self.canvas.yview)
        self.body = tk.Frame(self.canvas, bg=bg)
        self.body.bind("<Configure>", lambda e: self.canvas.configure(scrollregion=self.canvas.bbox("all")))
        self._win = self.canvas.create_window((0, 0), window=self.body, anchor="nw")
        self.canvas.bind("<Configure>", lambda e: self.canvas.itemconfigure(self._win, width=e.width))
        self.canvas.configure(yscrollcommand=self.scroll.set)
        self.canvas.pack(side="left", fill="both", expand=True)
        self.scroll.pack(side="right", fill="y")
        bind_wheel(self.canvas, self.canvas)
        bind_wheel(self.body, self.canvas)

    def bind_children(self):
        """Propaga a rolagem do mouse para todos os filhos ja criados."""
        def walk(widget):
            bind_wheel(widget, self.canvas)
            for child in widget.winfo_children():
                walk(child)
        walk(self.body)


def bind_wheel(widget, canvas):
    """Liga a roda do mouse (Windows, macOS e Linux) a rolagem do canvas."""
    def on_wheel(event):
        if getattr(event, "num", 0) == 4:
            delta = -1
        elif getattr(event, "num", 0) == 5:
            delta = 1
        else:
            delta = -1 if event.delta > 0 else 1
            if sys.platform == "darwin":
                delta = -event.delta
        canvas.yview_scroll(delta, "units")
        return "break"
    widget.bind("<MouseWheel>", on_wheel, add="+")
    widget.bind("<Button-4>", on_wheel, add="+")
    widget.bind("<Button-5>", on_wheel, add="+")


class Tooltip:
    """Dica exibida ao passar o mouse sobre um widget."""

    def __init__(self, widget, text, delay=600):
        self.widget, self.text, self.delay = widget, text, delay
        self.tip = None
        self.job = None
        widget.bind("<Enter>", self._schedule, add="+")
        widget.bind("<Leave>", self._hide, add="+")
        widget.bind("<ButtonPress>", self._hide, add="+")

    def _schedule(self, _event=None):
        self._cancel()
        self.job = self.widget.after(self.delay, self._show)

    def _cancel(self):
        if self.job:
            self.widget.after_cancel(self.job)
            self.job = None

    def _show(self):
        if self.tip or not self.text:
            return
        x = self.widget.winfo_rootx() + 12
        y = self.widget.winfo_rooty() + self.widget.winfo_height() + 6
        self.tip = tk.Toplevel(self.widget)
        self.tip.wm_overrideredirect(True)
        self.tip.configure(bg=C["border"])
        label = tk.Label(self.tip, text=self.text, bg=C["card"], fg=C["text"], font=FONT["small"],
                         justify="left", wraplength=360, padx=8, pady=5)
        label.pack(padx=1, pady=1)
        self.tip.wm_geometry(f"+{x}+{y}")

    def _hide(self, _event=None):
        self._cancel()
        if self.tip:
            self.tip.destroy()
            self.tip = None


def text_widget(master, height=6, mono=False, **kwargs):
    """Caixa de texto multilinha no tema escuro."""
    widget = tk.Text(master, height=height, bg=C["panel2"], fg=C["text"], insertbackground=C["text"],
                     selectbackground=C["accent"], selectforeground="#FFFFFF", relief="flat",
                     highlightthickness=1, highlightbackground=C["border"], highlightcolor=C["accent"],
                     font=FONT["mono"] if mono else FONT["base"], wrap="word" if not mono else "none",
                     padx=6, pady=4, **kwargs)
    return widget


def center_window(window, width, height, parent=None):
    window.update_idletasks()
    if parent is not None:
        x = parent.winfo_rootx() + (parent.winfo_width() - width) // 2
        y = parent.winfo_rooty() + (parent.winfo_height() - height) // 2
    else:
        x = (window.winfo_screenwidth() - width) // 2
        y = (window.winfo_screenheight() - height) // 3
    window.geometry(f"{width}x{height}+{max(0, x)}+{max(0, y)}")


class Dialog(tk.Toplevel):
    """Janela modal base com o tema do aplicativo."""

    def __init__(self, master, title, width=720, height=520):
        super().__init__(master)
        self.withdraw()
        self.title(title)
        self.configure(bg=C["panel"])
        self.transient(master.winfo_toplevel())
        self.result = None
        self.minsize(420, 300)
        center_window(self, width, height, master.winfo_toplevel())
        self.protocol("WM_DELETE_WINDOW", self.close)
        self.bind("<Escape>", lambda e: self.close())

    def show(self):
        self.deiconify()
        self.lift()
        try:
            self.grab_set()
        except tk.TclError:
            pass
        self.focus_set()
        self.wait_window(self)
        return self.result

    def close(self):
        try:
            self.grab_release()
        except tk.TclError:
            pass
        self.destroy()

    def buttons(self, parent, items):
        """Cria uma barra de botoes: items = [(texto, comando, estilo)]."""
        bar = ttk.Frame(parent)
        for text, command, style in reversed(items):
            ttk.Button(bar, text=text, command=command, style=style or "TButton").pack(side="right", padx=4)
        return bar
