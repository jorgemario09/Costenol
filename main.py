"""
IDE del Compilador Costeñol - Interfaz Gráfica Profesional.
Un entorno completo para escribir, compilar, depurar y ejecutar código en Costeñol.
"""
import tkinter as tk
from tkinter import ttk, filedialog, messagebox, simpledialog, font as tkfont
import threading
import re
import os
import sys

# Agregar el directorio al path
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from lexer import Lexer, Token
from parser_costenol import Parser
from interpreter import CostenolInterpreter, CostenolError

class Theme:
    @classmethod
    def set_dark(cls):
        cls.BG_DARK = "#1e1e2e"
        cls.BG_MEDIUM = "#252536"
        cls.BG_LIGHT = "#2d2d44"
        cls.BG_EDITOR = "#1a1a2e"
        cls.BG_LINE_NUMS = "#16162a"
        cls.FG_PRIMARY = "#e0e0e0"
        cls.FG_SECONDARY = "#a0a0b8"
        cls.FG_DIM = "#6c6c8a"
        cls.FG_LINE_NUM = "#5a5a7a"
        cls.ACCENT_PRIMARY = "#7c3aed"
        cls.ACCENT_SECONDARY = "#06b6d4"
        cls.ACCENT_SUCCESS = "#22c55e"
        cls.ACCENT_WARNING = "#f59e0b"
        cls.ACCENT_ERROR = "#ef4444"
        cls.BTN_RUN = "#22c55e"
        cls.BTN_RUN_HOVER = "#16a34a"
        cls.BTN_DEBUG = "#3b82f6"
        cls.BTN_DEBUG_HOVER = "#2563eb"
        cls.BTN_STOP = "#ef4444"
        cls.BTN_STOP_HOVER = "#dc2626"
        cls.BTN_NEW = "#8b5cf6"
        cls.BTN_NEW_HOVER = "#7c3aed"
        cls.SYN_KEYWORD = "#c084fc"
        cls.SYN_TYPE = "#22d3ee"
        cls.SYN_STRING = "#a3e635"
        cls.SYN_NUMBER = "#fb923c"
        cls.SYN_BOOL = "#f472b6"
        cls.SYN_COMMENT = "#6b7280"
        cls.SYN_FUNCTION = "#60a5fa"
        cls.SYN_OPERATOR = "#fbbf24"
        cls.SYN_VARIABLE = "#e0e0e0"
        cls.SYN_ERROR_BG = "#3b1111"
        cls.BORDER = "#3d3d5c"
        cls.SEPARATOR = "#3d3d5c"
        cls.SCROLLBAR_BG = "#2d2d44"
        cls.SCROLLBAR_FG = "#4a4a6a"
        cls.TAB_ACTIVE = "#7c3aed"
        cls.TAB_INACTIVE = "#252536"

    @classmethod
    def set_light(cls):
        cls.BG_DARK = "#e5e7eb"      # Gris claro para fondo general
        cls.BG_MEDIUM = "#f3f4f6"    # Gris un poco más claro
        cls.BG_LIGHT = "#ffffff"     # Blanco puro
        cls.BG_EDITOR = "#ffffff"    # Fondo del editor en blanco
        cls.BG_LINE_NUMS = "#f9fafb" # Fondo números de línea
        cls.FG_PRIMARY = "#1f2937"   # Texto principal oscuro
        cls.FG_SECONDARY = "#4b5563" # Texto secundario oscuro
        cls.FG_DIM = "#6b7280"       # Texto tenue
        cls.FG_LINE_NUM = "#9ca3af"  # Color de los números
        cls.ACCENT_PRIMARY = "#6d28d9" # Morado ajustado para modo claro
        cls.ACCENT_SECONDARY = "#0891b2" # Cian oscuro
        cls.ACCENT_SUCCESS = "#16a34a"
        cls.ACCENT_WARNING = "#d97706"
        cls.ACCENT_ERROR = "#dc2626"
        cls.BTN_RUN = "#16a34a"
        cls.BTN_RUN_HOVER = "#15803d"
        cls.BTN_DEBUG = "#2563eb"
        cls.BTN_DEBUG_HOVER = "#1d4ed8"
        cls.BTN_STOP = "#dc2626"
        cls.BTN_STOP_HOVER = "#b91c1c"
        cls.BTN_NEW = "#8b5cf6"
        cls.BTN_NEW_HOVER = "#7c3aed"
        
        # Colores de sintaxis adaptados a fondo blanco para que resalten
        cls.SYN_KEYWORD = "#7e22ce"
        cls.SYN_TYPE = "#0369a1"
        cls.SYN_STRING = "#4d7c0f"
        cls.SYN_NUMBER = "#c2410c"
        cls.SYN_BOOL = "#be185d"
        cls.SYN_COMMENT = "#6b7280"
        cls.SYN_FUNCTION = "#2563eb"
        cls.SYN_OPERATOR = "#b45309"
        cls.SYN_VARIABLE = "#1f2937"
        cls.SYN_ERROR_BG = "#fee2e2" # Rojo muy clarito para las líneas con error
        cls.BORDER = "#d1d5db"
        cls.SEPARATOR = "#d1d5db"
        cls.SCROLLBAR_BG = "#e5e7eb"
        cls.SCROLLBAR_FG = "#9ca3af"
        cls.TAB_ACTIVE = "#6d28d9"
        cls.TAB_INACTIVE = "#d1d5db"

# Inicializar tema oscuro por defecto al arrancar
Theme.set_dark()


class LineNumbers(tk.Canvas):
    def __init__(self, master, text_widget, **kwargs):
        super().__init__(master, **kwargs)
        self.text_widget = text_widget
        self.config(bg=Theme.BG_LINE_NUMS, highlightthickness=0, width=55, bd=0)
        self._error_lines = set()

    def set_error_lines(self, lines):
        self._error_lines = set(lines)
        self.redraw()

    def redraw(self):
        self.delete("all")
        i = self.text_widget.index("@0,0")
        while True:
            dline = self.text_widget.dlineinfo(i)
            if dline is None: break
            y = dline[1]
            linenum = str(i).split(".")[0]
            line_int = int(linenum)
            if line_int in self._error_lines:
                self.create_rectangle(0, y, 55, y + dline[3], fill=Theme.SYN_ERROR_BG, outline="")
                color = Theme.ACCENT_ERROR
            else:
                color = Theme.FG_LINE_NUM
            self.create_text(48, y, anchor="ne", text=linenum, fill=color, font=("Consolas", 11))
            i = self.text_widget.index(f"{i}+1line")

    def on_scroll(self, *args):
        self.redraw()

class CodeEditor(tk.Frame):
    def __init__(self, master, **kwargs):
        super().__init__(master, bg=Theme.BG_DARK, **kwargs)
        self.editor_frame = tk.Frame(self, bg=Theme.BG_DARK)
        self.editor_frame.pack(fill=tk.BOTH, expand=True)

        self.text = tk.Text(
            self.editor_frame, wrap=tk.NONE, bg=Theme.BG_EDITOR, fg=Theme.FG_PRIMARY,
            insertbackground=Theme.ACCENT_SECONDARY, selectbackground=Theme.ACCENT_PRIMARY,
            selectforeground="#ffffff", font=("Consolas", 13), undo=True,
            autoseparators=True, maxundo=-1, padx=10, pady=8, bd=0,
            highlightthickness=0, tabs=("4c",),
        )
        self.line_numbers = LineNumbers(self.editor_frame, self.text)
        self.v_scroll = ttk.Scrollbar(self.editor_frame, orient=tk.VERTICAL, command=self._on_vscroll)
        self.text.config(yscrollcommand=self._on_text_scroll)
        self.h_scroll = ttk.Scrollbar(self, orient=tk.HORIZONTAL, command=self.text.xview)
        self.text.config(xscrollcommand=self.h_scroll.set)

        self.line_numbers.pack(side=tk.LEFT, fill=tk.Y)
        self.text.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)
        self.v_scroll.pack(side=tk.RIGHT, fill=tk.Y)
        self.h_scroll.pack(side=tk.BOTTOM, fill=tk.X)

        self._setup_syntax_tags()

        self.text.bind('<KeyRelease>', self._on_key_release)
        self.text.bind('<ButtonRelease-1>', self._on_click)
        self.text.bind('<Configure>', self._on_configure)
        self.text.bind('<MouseWheel>', self._on_mousewheel)
        self.text.bind('<Tab>', self._on_tab)
        self.text.bind('(', lambda e: self._auto_close('(', ')'))
        self.text.bind('"', lambda e: self._auto_close_quote('"'))
        self._highlight_job = None

    def _setup_syntax_tags(self):
        self.text.tag_configure('keyword', foreground=Theme.SYN_KEYWORD, font=("Consolas", 13, "bold"))
        self.text.tag_configure('type', foreground=Theme.SYN_TYPE, font=("Consolas", 13, "bold"))
        self.text.tag_configure('string', foreground=Theme.SYN_STRING)
        self.text.tag_configure('number', foreground=Theme.SYN_NUMBER)
        self.text.tag_configure('bool', foreground=Theme.SYN_BOOL, font=("Consolas", 13, "bold"))
        self.text.tag_configure('comment', foreground=Theme.SYN_COMMENT, font=("Consolas", 13, "italic"))
        self.text.tag_configure('function', foreground=Theme.SYN_FUNCTION, font=("Consolas", 13, "bold"))
        self.text.tag_configure('operator', foreground=Theme.SYN_OPERATOR)
        self.text.tag_configure('error_line', background=Theme.SYN_ERROR_BG)

    def _on_tab(self, event):
        self.text.insert(tk.INSERT, "    ")
        return 'break'

    def _auto_close(self, open_char, close_char):
        self.text.insert(tk.INSERT, open_char + close_char)
        self.text.mark_set(tk.INSERT, f"{tk.INSERT}-1c")
        return 'break'

    def _auto_close_quote(self, char):
        next_char = self.text.get(tk.INSERT)
        if next_char == char:
            self.text.mark_set(tk.INSERT, f"{tk.INSERT}+1c")
            return 'break'
        self.text.insert(tk.INSERT, char + char)
        self.text.mark_set(tk.INSERT, f"{tk.INSERT}-1c")
        return 'break'

    def _on_key_release(self, event=None):
        self.line_numbers.redraw()
        self._schedule_highlight()

    def _on_click(self, event=None): self.line_numbers.redraw()
    def _on_configure(self, event=None): self.line_numbers.redraw()
    def _on_mousewheel(self, event=None): self.after(10, self.line_numbers.redraw)

    def _on_vscroll(self, *args):
        self.text.yview(*args)
        self.line_numbers.redraw()

    def _on_text_scroll(self, *args):
        self.v_scroll.set(*args)
        self.line_numbers.redraw()

    def _schedule_highlight(self):
        if self._highlight_job: self.after_cancel(self._highlight_job)
        self._highlight_job = self.after(150, self.highlight_syntax)

    def highlight_syntax(self):
        code = self.text.get("1.0", tk.END)
        for tag in ('keyword', 'type', 'string', 'number', 'bool', 'comment', 'function', 'operator'):
            self.text.tag_remove(tag, "1.0", tk.END)

        patterns = [
            ('comment', r'//.*?//', re.DOTALL),
            ('string', r'"[^"]*"', 0),
            ('function', r'\bMensaje\.Texto\b', 0),
            ('function', r'\bCaptura\.(Entero|Real|Logico|Texto)\b', 0),
            ('keyword', r'\b(Si|Sino|FinSi|Mientras|FinMientras)\b', 0),
            ('type', r'\b(Entero|Real|Logico|Texto)\b', 0),
            ('bool', r'\b(Verdadero|Falso)\b', 0),
            ('number', r'\b\d+[,\.]\d+\b', 0),
            ('number', r'\b\d+\b', 0),
            ('operator', r'[+\-*/=<>!]+', 0),
        ]
        for tag, pattern, flags in patterns:
            for match in re.finditer(pattern, code, flags):
                self.text.tag_add(tag, f"1.0+{match.start()}c", f"1.0+{match.end()}c")
        self.text.tag_raise('string')
        self.text.tag_raise('comment')

    def get_code(self): return self.text.get("1.0", tk.END).rstrip('\n')

    def set_code(self, code):
        self.text.delete("1.0", tk.END)
        self.text.insert("1.0", code)
        self.highlight_syntax()
        self.line_numbers.redraw()

    def mark_error_lines(self, lines):
        self.text.tag_remove('error_line', "1.0", tk.END)
        self.line_numbers.set_error_lines(lines)
        for line in lines: self.text.tag_add('error_line', f"{line}.0", f"{line}.end")

    def clear_errors(self):
        self.text.tag_remove('error_line', "1.0", tk.END)
        self.line_numbers.set_error_lines(set())

    def goto_line(self, line):
        self.text.mark_set(tk.INSERT, f"{line}.0")
        self.text.see(f"{line}.0")
        self.text.focus_set()

class OutputPanel(tk.Frame):
    def __init__(self, master, editor=None, **kwargs):
        super().__init__(master, bg=Theme.BG_MEDIUM, **kwargs)
        self.editor = editor
        self.tab_frame = tk.Frame(self, bg=Theme.BG_DARK, height=36)
        self.tab_frame.pack(fill=tk.X)
        self.tab_frame.pack_propagate(False)

        self.tabs = {}
        self.current_tab = None
        self.panels = {}
        self.panel_container = tk.Frame(self, bg=Theme.BG_MEDIUM)
        self.panel_container.pack(fill=tk.BOTH, expand=True)

        for tab_name in ['Consola', 'Errores', 'Tokens', 'Depuración']:
            self._create_tab(tab_name)
            panel = tk.Text(
                self.panel_container, wrap=tk.WORD, bg=Theme.BG_MEDIUM, fg=Theme.FG_PRIMARY,
                font=("Consolas", 11), bd=0, highlightthickness=0, padx=12, pady=8,
                state=tk.DISABLED, cursor="arrow",
            )
            panel.tag_configure('error', foreground=Theme.ACCENT_ERROR)
            panel.tag_configure('warning', foreground=Theme.ACCENT_WARNING)
            panel.tag_configure('success', foreground=Theme.ACCENT_SUCCESS)
            panel.tag_configure('info', foreground=Theme.ACCENT_SECONDARY)
            panel.tag_configure('header', foreground=Theme.ACCENT_PRIMARY, font=("Consolas", 11, "bold"))
            panel.tag_configure('dim', foreground=Theme.FG_DIM)

            if tab_name == 'Errores':
                panel.bind('<Button-1>', self._on_error_click)
                panel.config(cursor="hand2")
            self.panels[tab_name] = panel

        self.select_tab('Consola')

    def _create_tab(self, name):
        btn = tk.Label(self.tab_frame, text=f"  {name}  ", bg=Theme.TAB_INACTIVE, fg=Theme.FG_SECONDARY, font=("Segoe UI", 10), padx=12, pady=6, cursor="hand2")
        btn.pack(side=tk.LEFT, padx=(1, 0))
        btn.bind('<Button-1>', lambda e, n=name: self.select_tab(n))
        self.tabs[name] = btn

    def select_tab(self, name):
        if self.current_tab:
            self.panels[self.current_tab].pack_forget()
            self.tabs[self.current_tab].config(bg=Theme.TAB_INACTIVE, fg=Theme.FG_SECONDARY)
        self.current_tab = name
        self.panels[name].pack(fill=tk.BOTH, expand=True)
        self.tabs[name].config(bg=Theme.TAB_ACTIVE, fg="#ffffff")

    def _on_error_click(self, event):
        if not self.editor: return
        panel = self.panels['Errores']
        index = panel.index(f"@{event.x},{event.y}")
        line_content = panel.get(f"{index} linestart", f"{index} lineend")
        match = re.search(r'Línea\s+(\d+)', line_content)
        if match: self.editor.goto_line(int(match.group(1)))

    def write(self, text, tag=None, panel_name=None):
        target = panel_name or self.current_tab
        panel = self.panels.get(target, self.panels['Consola'])
        panel.config(state=tk.NORMAL)
        if tag: panel.insert(tk.END, text, tag)
        else: panel.insert(tk.END, text)
        panel.see(tk.END)
        panel.config(state=tk.DISABLED)

    def clear(self, panel_name=None):
        if panel_name:
            panel = self.panels[panel_name]
            panel.config(state=tk.NORMAL)
            panel.delete("1.0", tk.END)
            panel.config(state=tk.DISABLED)
        else:
            for panel in self.panels.values():
                panel.config(state=tk.NORMAL)
                panel.delete("1.0", tk.END)
                panel.config(state=tk.DISABLED)

class StatusBar(tk.Frame):
    def __init__(self, master, **kwargs):
        super().__init__(master, bg=Theme.ACCENT_PRIMARY, height=26, **kwargs)
        self.pack_propagate(False)
        self.line_col_label = tk.Label(self, text="Línea 1, Col 1", bg=Theme.ACCENT_PRIMARY, fg="#ffffff", font=("Segoe UI", 9), padx=12)
        self.line_col_label.pack(side=tk.RIGHT)
        self.status_label = tk.Label(self, text="Listo", bg=Theme.ACCENT_PRIMARY, fg="#ffffff", font=("Segoe UI", 9), padx=12)
        self.status_label.pack(side=tk.LEFT)
        self.file_label = tk.Label(self, text="Sin archivo", bg=Theme.ACCENT_PRIMARY, fg="#ffffff", font=("Segoe UI", 9), padx=12)
        self.file_label.pack(side=tk.LEFT)

    def update_cursor(self, line, col): self.line_col_label.config(text=f"Línea {line}, Col {col}")
    def set_file(self, filename): self.file_label.config(text=filename)

    def set_status(self, text, color=None):
        self.status_label.config(text=text)
        if color:
            self.config(bg=color)
            self.line_col_label.config(bg=color)
            self.status_label.config(bg=color)
            self.file_label.config(bg=color)

class CostenolIDE(tk.Tk):
    def __init__(self):
        super().__init__()
        self.title("Costeñol IDE — Compilador del Lenguaje Costeñol")
        self.geometry("1280x800")
        self.minsize(900, 600)
        self.configure(bg=Theme.BG_DARK)
        self.current_file = None
        self._running = False
        self._interpreter = None
        self._input_event = None
        self._input_value = None

        self._setup_styles()
        self._create_menu() # <--- Llamada al nuevo menú de arriba
        self._create_toolbar()
        self._create_main_area()
        self._create_status_bar()
        
        self.editor.set_code("")

        self.bind('<F5>', lambda e: self.run_code())
        self.bind('<F6>', lambda e: self.debug_code())
        self.bind('<Escape>', lambda e: self.stop_execution())
        self.editor.text.bind('<KeyRelease>', self._update_cursor_pos)
        self.editor.text.bind('<ButtonRelease-1>', self._update_cursor_pos)
        self._center_window()

    def _setup_styles(self):
        style = ttk.Style()
        style.theme_use('clam')
        style.configure("Vertical.TScrollbar", background=Theme.SCROLLBAR_FG, troughcolor=Theme.SCROLLBAR_BG, borderwidth=0, arrowsize=0)
        style.configure("Horizontal.TScrollbar", background=Theme.SCROLLBAR_FG, troughcolor=Theme.SCROLLBAR_BG, borderwidth=0, arrowsize=0)

    def _center_window(self):
        self.update_idletasks()
        w, h = self.winfo_width(), self.winfo_height()
        sw, sh = self.winfo_screenwidth(), self.winfo_screenheight()
        self.geometry(f"{w}x{h}+{(sw - w) // 2}+{(sh - h) // 2}")
        
    def _create_menu(self):
        """Crea el menú principal superior para cambiar el tema."""
        self.menubar = tk.Menu(self)
        
        opciones_menu = tk.Menu(self.menubar, tearoff=0)
        
        tema_menu = tk.Menu(opciones_menu, tearoff=0)
        tema_menu.add_command(label="🌙 Modo Oscuro", command=lambda: self.change_theme("dark"))
        tema_menu.add_command(label="☀️ Modo Claro", command=lambda: self.change_theme("light"))
        
        opciones_menu.add_cascade(label="Apariencia / Tema", menu=tema_menu)
        self.menubar.add_cascade(label="Opciones", menu=opciones_menu)
        
        self.config(menu=self.menubar)
        
    def change_theme(self, mode):
        """Repinta toda la interfaz gráfica en vivo sin perder el código."""
        if self._running:
            messagebox.showwarning("¡Ey llave!", "No puedes cambiar el tema mientras el código se está ejecutando. Detenlo primero.")
            return

        # 1. Guardar el código actual
        current_code = self.editor.get_code()
        
        # 2. Cambiar los colores en la clase Theme
        if mode == "light":
            Theme.set_light()
        else:
            Theme.set_dark()
            
        # 3. Destruir los contenedores gráficos actuales
        if hasattr(self, 'toolbar'): self.toolbar.destroy()
        if hasattr(self, 'paned'): self.paned.destroy()
        if hasattr(self, 'status_bar'): self.status_bar.destroy()
        
        # 4. Volver a pintar el fondo principal
        self.configure(bg=Theme.BG_DARK)
        
        # 5. Volver a crear la interfaz (ahora nacerá con los colores nuevos)
        self._create_toolbar()
        self._create_main_area()
        self._create_status_bar()
        
        # 6. Devolverle el código al editor y reconfigurar eventos
        self.editor.set_code(current_code)
        self.editor.text.bind('<KeyRelease>', self._update_cursor_pos)
        self.editor.text.bind('<ButtonRelease-1>', self._update_cursor_pos)

    def _create_toolbar(self):
        self.toolbar = tk.Frame(self, bg=Theme.BG_DARK, height=56)
        self.toolbar.pack(fill=tk.X, side=tk.TOP)
        self.toolbar.pack_propagate(False)

        title_frame = tk.Frame(self.toolbar, bg=Theme.BG_DARK)
        title_frame.pack(side=tk.LEFT, padx=16)
        tk.Label(title_frame, text="🌴", bg=Theme.BG_DARK, fg=Theme.ACCENT_PRIMARY, font=("Segoe UI Emoji", 20)).pack(side=tk.LEFT, padx=(0, 6))
        tk.Label(title_frame, text="Costeñol IDE", bg=Theme.BG_DARK, fg=Theme.FG_PRIMARY, font=("Segoe UI", 16, "bold")).pack(side=tk.LEFT)

        tk.Frame(self.toolbar, bg=Theme.SEPARATOR, width=1).pack(side=tk.LEFT, fill=tk.Y, padx=16, pady=12)
        exec_frame = tk.Frame(self.toolbar, bg=Theme.BG_DARK)
        exec_frame.pack(side=tk.LEFT)

        self._create_tool_button(exec_frame, "▶  Ejecutar", self.run_code, Theme.BTN_RUN, "#ffffff", Theme.BTN_RUN_HOVER)
        self._create_tool_button(exec_frame, "🔍  Depurar", self.debug_code, Theme.BTN_DEBUG, "#ffffff", Theme.BTN_DEBUG_HOVER)
        self._create_tool_button(exec_frame, "⏹ Detener", self.stop_execution, Theme.BTN_STOP, "#ffffff", Theme.BTN_STOP_HOVER)

    def _create_tool_button(self, parent, text, command, bg, fg, hover_bg=None):
        btn = tk.Label(parent, text=text, bg=bg, fg=fg, font=("Segoe UI", 10, "bold"), padx=14, pady=6, cursor="hand2")
        btn.pack(side=tk.LEFT, padx=3, pady=8)
        if not hover_bg: hover_bg = Theme.BG_MEDIUM
        btn.bind('<Button-1>', lambda e: command())
        btn.bind('<Enter>', lambda e: btn.config(bg=hover_bg))
        btn.bind('<Leave>', lambda e: btn.config(bg=bg))
        return btn

    def _create_main_area(self):
        self.paned = tk.PanedWindow(self, orient=tk.VERTICAL, bg=Theme.BG_DARK, sashwidth=4, sashrelief=tk.FLAT, sashpad=0)
        self.paned.pack(fill=tk.BOTH, expand=True)
        self.editor = CodeEditor(self.paned)
        self.paned.add(self.editor, minsize=200)
        self.output = OutputPanel(self.paned, editor=self.editor)
        self.paned.add(self.output, minsize=100)
        self.after(100, lambda: self.paned.sash_place(0, 0, 520))

    def _create_status_bar(self):
        self.status_bar = StatusBar(self)
        self.status_bar.pack(fill=tk.X, side=tk.BOTTOM)

    def _update_cursor_pos(self, event=None):
        pos = self.editor.text.index(tk.INSERT)
        line, col = pos.split('.')
        self.status_bar.update_cursor(line, int(col) + 1)

    def run_code(self):
        if not self._running: self._compile_and_run(debug_mode=False)

    def debug_code(self):
        if not self._running: self._compile_and_run(debug_mode=True)

    def stop_execution(self):
        if self._interpreter: self._interpreter.stop()
        self._running = False
        if self._input_event:
            self._input_value = None
            self._input_event.set()
        self.status_bar.set_status("Detenido", Theme.ACCENT_WARNING)

    def _compile_and_run(self, debug_mode=False):
        self._running = True
        self.editor.clear_errors()
        self.output.clear()

        code = self.editor.get_code()
        if not code.strip():
            self.output.write("No hay código pa' compilar.\n", 'warning', 'Consola')
            self._running = False
            return

        self.status_bar.set_status("Analizando léxico...", Theme.ACCENT_SECONDARY)
        self.update()

        lexer = Lexer(code)
        tokens, lex_errors = lexer.tokenize()

        if debug_mode:
            self.output.write("═══ ANÁLISIS LÉXICO ═══\n\n", 'header', 'Tokens')
            if tokens:
                for tok in tokens:
                    self.output.write(f"  {tok.type:20s}  {repr(tok.value):25s}  Línea {tok.line}, Col {tok.column}\n", 'dim', 'Tokens')

        self.status_bar.set_status("Analizando sintaxis...", Theme.ACCENT_SECONDARY)
        self.update()

        parser = Parser(tokens)
        ast, parse_errors = parser.parse()

        all_errors = lex_errors + parse_errors
        if all_errors:
            self.output.select_tab('Errores')
            self.output.write(f"═══ ¡ECHE! SE ENCONTRARON {len(all_errors)} ERROR(ES) ═══\n\n", 'header', 'Errores')
            error_lines = set()
            for err in all_errors:
                self.output.write(f"  ❌ {err}\n\n", 'error', 'Errores')
                match = re.search(r'Línea\s+(\d+)', err)
                if match: error_lines.add(int(match.group(1)))

            self.editor.mark_error_lines(error_lines)
            self.status_bar.set_status(f"{len(all_errors)} error(es) encontrado(s)", Theme.ACCENT_ERROR)
            self._running = False
            return

        self.output.select_tab('Consola')
        self.status_bar.set_status("Ejecutando...", Theme.ACCENT_SUCCESS)
        self.update()

        self.output.write("EJECUCIÓN DEL PROGRAMA\n\n", 'header', 'Consola')

        def output_func(text):
            self.output.write(str(text) + "\n", panel_name='Consola')
            self.update()

        def input_func(prompt):
            self._input_event = threading.Event()
            self._input_value = None
            self.after(0, lambda: self._show_input_dialog(prompt))
            self._input_event.wait()
            return self._input_value

        self._interpreter = CostenolInterpreter(ast, parser.symbol_table, input_func=input_func, output_func=output_func)
        threading.Thread(target=self._run_interpreter, daemon=True).start()

    def _show_input_dialog(self, prompt):
        result = simpledialog.askstring("Captura de Datos — Costeñol", prompt, parent=self)
        self._input_value = result
        self._input_event.set()

    def _run_interpreter(self):
        try:
            self._interpreter.run()
            if not self._interpreter._stopped:
                self.after(0, lambda: self._execution_finished(True))
            else:
                self.after(0, lambda: self._execution_finished(False, "Ejecución frenada por ti mismo."))
        except Exception as e:
            self.after(0, lambda: self._execution_finished(False, str(e)))

    def _execution_finished(self, success, error_msg=None):
        self._running = False
        if success:
            self.output.write("\n¡TODO FIRME! EL PROGRAMA TERMINÓ MELO \n", 'success', 'Consola')
            self.status_bar.set_status("Ejecución completada ✓", Theme.ACCENT_SUCCESS)
        else:
            if error_msg: self.output.write(f"\n❌ {error_msg}\n", 'error', 'Consola')
            self.status_bar.set_status("Ejecución fallida", Theme.ACCENT_ERROR)

def main():
    app = CostenolIDE()
    app.mainloop()

if __name__ == "__main__":
    main()