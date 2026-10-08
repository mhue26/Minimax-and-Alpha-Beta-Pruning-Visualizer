# Alpha-Beta / Minimax Visualizer
#
# Run:
#     python alphabeta_visualizer.py
#
# Set depth, branching factor, and the random integer range for leaves, then
# click New Tree. Choose Minimax or Alpha-Beta and click Run. Step through
# the trace with Prev / Next, or press Play to animate. The status bar keeps
# a running record of alpha and beta (alpha-beta mode). Every algorithm step
# is labeled in the log. Left/Right arrow keys step; Space toggles play.

import math
import random
import tkinter as tk
import tkinter.font as tkfont
from tkinter import messagebox, ttk

DEPTH_MIN, DEPTH_MAX = 1, 5
BRANCH_MIN, BRANCH_MAX = 2, 4
LEAF_BOUND = 999

COLOR_BG = "#eef1f6"
COLOR_CARD = "#ffffff"
COLOR_CANVAS = "#f8f9fc"
COLOR_LINE = "#e4e8f0"
COLOR_INK = "#111111"
COLOR_EMPHASIS = "#111111"
COLOR_EMPHASIS_ACTIVE = "#000000"
COLOR_CHIP = "#eef1f6"
COLOR_CHIP_FLASH = "#fff1df"
COLOR_EDGE = "#9aa3b2"
COLOR_EDGE_PRUNED = "#c5cad3"
COLOR_MAX = "#dce8ff"
COLOR_MIN = "#ffe0dc"
COLOR_MAX_INK = "#1f5aa8"
COLOR_MIN_INK = "#b13d36"
COLOR_MAX_DEEP = "#b9d4fb"
COLOR_MIN_DEEP = "#f6c2be"
COLOR_IDLE = "#ffffff"
COLOR_ACTIVE = "#ffe7a3"
COLOR_PRUNED = "#e4e4e6"
COLOR_OUTLINE = "#2c3138"
COLOR_ACTIVE_OUTLINE = "#e09b00"
COLOR_TEXT = "#1c1e21"
COLOR_MUTED = "#6b7078"
COLOR_FLASH = "#c45c00"

NODE_R = 24
X_GAP = 64
Y_GAP = 90


def pick_font(size, weight="normal"):
    available = set(tkfont.families())
    for name in ("Avenir Next", "Avenir", "Helvetica Neue", "Helvetica"):
        if name in available:
            if weight == "normal":
                return (name, size)
            return (name, size, weight)
    if weight == "normal":
        return ("TkDefaultFont", size)
    return ("TkDefaultFont", size, weight)


def step_glyph(event):
    kind = event["type"]
    if kind == "enter":
        return "↓"
    if kind == "exit":
        return "↑"
    if kind == "leaf":
        return "●"
    if kind == "prune":
        return "✕"
    which = event.get("which")
    if which == "alpha":
        return "α"
    if which == "beta":
        return "β"
    return "◆"


def step_bounds(event):
    if "alpha" not in event:
        return "—", "—"
    return fmt(event["alpha"]), fmt(event["beta"])


def fmt(value):
    if value is None:
        return "—"
    if value == math.inf:
        return "+∞"
    if value == -math.inf:
        return "−∞"
    if isinstance(value, float) and value.is_integer():
        return str(int(value))
    return str(value)


class Node:
    def __init__(self, is_max, path):
        self.is_max = is_max
        self.path = path
        self.children = []
        self.value = None
        self.shown_value = None
        self.x = 0
        self.y = 0
        self.visited = False
        self.pruned = False
        self.prune_root = False
        self.active = False

    @property
    def is_leaf(self):
        return not self.children

    def role(self):
        if self.is_leaf:
            return "LEAF"
        return "MAX" if self.is_max else "MIN"

    def name(self):
        return f"{self.role()} {self.path}"


def build_tree(depth, branching, leaf_min, leaf_max):
    """Full uniform tree. Leaves get random integers; internals start unevaluated."""

    def grow(level, is_max, path):
        node = Node(is_max, path)
        if level == depth:
            node.value = random.randint(leaf_min, leaf_max)
            node.shown_value = node.value
            return node
        for i in range(branching):
            child_path = str(i) if path == "root" else f"{path}.{i}"
            node.children.append(grow(level + 1, not is_max, child_path))
        return node

    return grow(0, True, "root")


def layout_tree(root):
    """Place nodes by leaf order. Returns (width, height) of the layout."""
    cursor = [40]

    def place(node, depth):
        node.y = 36 + depth * Y_GAP
        if node.is_leaf:
            node.x = cursor[0]
            cursor[0] += X_GAP
            return
        for child in node.children:
            place(child, depth + 1)
        node.x = sum(child.x for child in node.children) / len(node.children)

    place(root, 0)
    width = max(cursor[0] + 20, 400)
    height = 36 + max_depth(root) * Y_GAP + 70
    return width, height


def max_depth(node):
    if node.is_leaf:
        return 0
    return 1 + max(max_depth(child) for child in node.children)


def minimax_record(node, events):
    """Record plain minimax as labeled events. Does not draw."""
    events.append({
        "type": "enter",
        "node": node,
        "label": f"Enter {node.name()}",
    })
    if node.is_leaf:
        events.append({
            "type": "leaf",
            "node": node,
            "value": node.value,
            "label": f"Leaf {node.path} = {fmt(node.value)}",
        })
        events.append({
            "type": "exit",
            "node": node,
            "value": node.value,
            "label": f"Return {fmt(node.value)} from {node.name()}",
        })
        return node.value

    value = -math.inf if node.is_max else math.inf
    for child in node.children:
        child_value = minimax_record(child, events)
        if node.is_max:
            improved = child_value > value
            value = child_value if improved else value
            if improved:
                label = f"{node.name()} value ← {fmt(value)}"
            else:
                label = (
                    f"{node.name()} keeps {fmt(value)} "
                    f"(child {fmt(child_value)} is smaller)"
                )
        else:
            improved = child_value < value
            value = child_value if improved else value
            if improved:
                label = f"{node.name()} value ← {fmt(value)}"
            else:
                label = (
                    f"{node.name()} keeps {fmt(value)} "
                    f"(child {fmt(child_value)} is larger)"
                )
        events.append({
            "type": "update",
            "node": node,
            "which": "value",
            "value": value,
            "label": label,
        })
    events.append({
        "type": "exit",
        "node": node,
        "value": value,
        "label": f"Return {fmt(value)} from {node.name()}",
    })
    return value


def alphabeta_record(node, alpha, beta, events):
    """Record alpha-beta (AIMA order) as labeled events. Does not draw."""
    events.append({
        "type": "enter",
        "node": node,
        "alpha": alpha,
        "beta": beta,
        "label": f"Enter {node.name()}",
    })
    if node.is_leaf:
        events.append({
            "type": "leaf",
            "node": node,
            "value": node.value,
            "alpha": alpha,
            "beta": beta,
            "label": f"Leaf {node.path} = {fmt(node.value)}",
        })
        events.append({
            "type": "exit",
            "node": node,
            "value": node.value,
            "alpha": alpha,
            "beta": beta,
            "label": f"Return {fmt(node.value)} from {node.name()}",
        })
        return node.value

    if node.is_max:
        value = -math.inf
        for index, child in enumerate(node.children):
            child_value = alphabeta_record(child, alpha, beta, events)
            improved = child_value > value
            value = child_value if improved else value
            if improved:
                label = f"{node.name()} value ← {fmt(value)}"
            else:
                label = (
                    f"{node.name()} keeps {fmt(value)} "
                    f"(child {fmt(child_value)} is smaller)"
                )
            events.append({
                "type": "update",
                "node": node,
                "which": "value",
                "value": value,
                "alpha": alpha,
                "beta": beta,
                "label": label,
            })
            if value >= beta:
                for sibling in node.children[index + 1:]:
                    events.append({
                        "type": "prune",
                        "node": sibling,
                        "alpha": alpha,
                        "beta": beta,
                        "value": value,
                        "label": (
                            f"Prune {sibling.name()}: β ≤ α "
                            f"(value {fmt(value)} ≥ β {fmt(beta)})"
                        ),
                    })
                break
            if value > alpha:
                alpha = value
                events.append({
                    "type": "update",
                    "node": node,
                    "which": "alpha",
                    "value": value,
                    "alpha": alpha,
                    "beta": beta,
                    "label": f"α ← {fmt(alpha)} at {node.name()}",
                })
    else:
        value = math.inf
        for index, child in enumerate(node.children):
            child_value = alphabeta_record(child, alpha, beta, events)
            improved = child_value < value
            value = child_value if improved else value
            if improved:
                label = f"{node.name()} value ← {fmt(value)}"
            else:
                label = (
                    f"{node.name()} keeps {fmt(value)} "
                    f"(child {fmt(child_value)} is larger)"
                )
            events.append({
                "type": "update",
                "node": node,
                "which": "value",
                "value": value,
                "alpha": alpha,
                "beta": beta,
                "label": label,
            })
            if value <= alpha:
                for sibling in node.children[index + 1:]:
                    events.append({
                        "type": "prune",
                        "node": sibling,
                        "alpha": alpha,
                        "beta": beta,
                        "value": value,
                        "label": (
                            f"Prune {sibling.name()}: β ≤ α "
                            f"(value {fmt(value)} ≤ α {fmt(alpha)})"
                        ),
                    })
                break
            if value < beta:
                beta = value
                events.append({
                    "type": "update",
                    "node": node,
                    "which": "beta",
                    "value": value,
                    "alpha": alpha,
                    "beta": beta,
                    "label": f"β ← {fmt(beta)} at {node.name()}",
                })

    events.append({
        "type": "exit",
        "node": node,
        "value": value,
        "alpha": alpha,
        "beta": beta,
        "label": f"Return {fmt(value)} from {node.name()}",
    })
    return value


class VisualizerApp:
    def __init__(self, win):
        self.win = win
        win.title("Minimax & Alpha-Beta Visualizer")
        win.configure(background=COLOR_BG)
        win.minsize(960, 640)

        self.mode = tk.StringVar(value="alphabeta")
        self.depth_var = tk.IntVar(value=3)
        self.branch_var = tk.IntVar(value=2)
        self.leaf_min_var = tk.IntVar(value=-20)
        self.leaf_max_var = tk.IntVar(value=20)
        self.speed_var = tk.IntVar(value=6)

        self.root = None
        self.events = []
        self.step = -1
        self.playing = False
        self.after_id = None
        self.alpha = None
        self.beta = None
        self.flash = None
        self.prune_count = 0
        self.active_node = None
        self.current_label = "Build a tree, choose a mode, then click Run."
        self._drawing = False
        self._view_size = (0, 0)
        self._configure_after = None
        self.node_font = pick_font(12, "bold")
        self.node_font_active = pick_font(15, "bold")
        self.badge_font = pick_font(13, "bold")
        self.log_font = pick_font(12)
        self.log_font_bold = pick_font(12, "bold")
        self.small_font = pick_font(8)
        self.ui_font = pick_font(13)
        self.ui_font_bold = pick_font(13, "bold")
        self.ui_small = pick_font(11)
        self.panel_font = pick_font(11)
        self.panel_small = pick_font(10)

        self._apply_theme()
        self._build_controls()
        self._build_status()
        self._build_canvas()
        self.new_tree()
        self.mode.trace_add("write", self._on_mode_change)

        win.bind("<Left>", self._on_left)
        win.bind("<Right>", self._on_right)
        win.bind("<space>", self._on_space)
        win.protocol("WM_DELETE_WINDOW", self.on_close)

    def _typing_focus(self, widget):
        return isinstance(widget, (tk.Spinbox, tk.Entry, ttk.Spinbox, ttk.Entry))

    def _on_left(self, event):
        if self._typing_focus(event.widget):
            return
        self.prev_step()
        return "break"

    def _on_right(self, event):
        if self._typing_focus(event.widget):
            return
        self.next_step()
        return "break"

    def _on_space(self, event):
        if isinstance(event.widget, (tk.Button, ttk.Button)):
            return
        self.toggle_play()
        return "break"

    def _on_mode_change(self, *_args):
        self._paint_mode()
        if not self.events:
            self._refresh_status()
            return
        self._stop_playback()
        self.events = []
        self.step = -1
        self._reset_visual()
        name = "Alpha-beta" if self.mode.get() == "alphabeta" else "Minimax"
        self.current_label = f"Switched to {name}. Click Run to record this algorithm."
        self._refresh()

    def _apply_theme(self):
        style = ttk.Style(self.win)
        if "clam" in style.theme_names():
            style.theme_use("clam")
        style.configure(".", background=COLOR_BG, foreground=COLOR_TEXT, font=self.ui_font)
        style.configure("TFrame", background=COLOR_BG)
        style.configure("Card.TFrame", background=COLOR_CARD)
        style.configure("TLabel", background=COLOR_BG, foreground=COLOR_TEXT, font=self.ui_font)
        style.configure("Card.TLabel", background=COLOR_CARD, foreground=COLOR_TEXT, font=self.ui_font)
        style.configure(
            "Muted.TLabel", background=COLOR_CARD, foreground=COLOR_MUTED, font=self.ui_small,
        )
        style.configure(
            "TSpinbox",
            fieldbackground=COLOR_CARD,
            background=COLOR_CARD,
            foreground=COLOR_INK,
            arrowsize=11,
            bordercolor="#c5cad3",
            lightcolor=COLOR_CARD,
            darkcolor="#c5cad3",
            font=self.panel_font,
        )
        style.map(
            "TSpinbox",
            foreground=[("!disabled", COLOR_INK)],
            fieldbackground=[("!disabled", COLOR_CARD)],
        )
        flat_layout = [
            ("Button.padding", {"sticky": "nswe", "children": [
                ("Button.label", {"sticky": "nswe"}),
            ]}),
        ]
        style.layout("New.TButton", flat_layout)
        style.layout("Run.TButton", flat_layout)
        style.layout("ModeOn.TButton", flat_layout)
        style.layout("ModeOff.TButton", flat_layout)
        style.configure(
            "ModeOn.TButton",
            background=COLOR_EMPHASIS,
            foreground="#ffffff",
            font=self.panel_font,
            padding=(8, 4),
            borderwidth=0,
            relief="flat",
            focuscolor=COLOR_EMPHASIS,
        )
        style.map(
            "ModeOn.TButton",
            background=[("pressed", COLOR_EMPHASIS_ACTIVE), ("active", "#2a2a2a"), ("!disabled", COLOR_EMPHASIS)],
            foreground=[("!disabled", "#ffffff")],
            relief=[("!disabled", "flat")],
        )
        style.configure(
            "ModeOff.TButton",
            background="#f4f5f7",
            foreground=COLOR_INK,
            font=self.panel_font,
            padding=(8, 4),
            borderwidth=0,
            relief="flat",
            focuscolor="#f4f5f7",
        )
        style.map(
            "ModeOff.TButton",
            background=[("pressed", "#e6e8ec"), ("active", "#eceef2"), ("!disabled", "#f4f5f7")],
            foreground=[("!disabled", COLOR_INK)],
            relief=[("!disabled", "flat")],
        )
        style.configure(
            "New.TButton",
            background="#f4f5f7",
            foreground=COLOR_INK,
            font=self.panel_font,
            padding=(10, 4),
            borderwidth=0,
            relief="flat",
            focuscolor="#f4f5f7",
        )
        style.map(
            "New.TButton",
            background=[("pressed", "#e6e8ec"), ("active", "#eceef2"), ("!disabled", "#f4f5f7")],
            foreground=[("!disabled", COLOR_INK)],
            relief=[("!disabled", "flat")],
        )
        style.configure(
            "Run.TButton",
            background=COLOR_EMPHASIS,
            foreground="#ffffff",
            font=self.panel_font,
            padding=(10, 4),
            borderwidth=0,
            relief="flat",
            focuscolor=COLOR_EMPHASIS,
        )
        style.map(
            "Run.TButton",
            background=[
                ("pressed", COLOR_EMPHASIS_ACTIVE),
                ("active", "#2a2a2a"),
                ("!disabled", COLOR_EMPHASIS),
            ],
            foreground=[("!disabled", "#ffffff")],
            relief=[("!disabled", "flat")],
        )
        style.configure(
            "Emphasis.TButton",
            background=COLOR_EMPHASIS,
            foreground="#ffffff",
            font=self.panel_font,
            padding=(8, 1),
            borderwidth=0,
            focuscolor=COLOR_EMPHASIS,
        )
        style.map(
            "Emphasis.TButton",
            background=[
                ("pressed", COLOR_EMPHASIS_ACTIVE),
                ("active", "#2a2a2a"),
                ("!disabled", COLOR_EMPHASIS),
            ],
            foreground=[("!disabled", "#ffffff")],
        )
        style.configure(
            "Quiet.TButton",
            background="#f4f5f7",
            foreground=COLOR_INK,
            font=self.panel_font,
            padding=(8, 1),
            borderwidth=1,
            bordercolor="#b7bec8",
            focuscolor="#f4f5f7",
        )
        style.map(
            "Quiet.TButton",
            background=[("pressed", "#e6e8ec"), ("active", "#eceef2"), ("!disabled", "#f4f5f7")],
            foreground=[("!disabled", COLOR_INK)],
        )
        style.layout("Arrow.TButton", flat_layout)
        style.layout("Play.TButton", flat_layout)
        style.configure(
            "Arrow.TButton",
            background="#f4f5f7",
            foreground=COLOR_INK,
            font=self.panel_small,
            padding=(0, 3),
            borderwidth=0,
            relief="flat",
            focuscolor="#f4f5f7",
        )
        style.map(
            "Arrow.TButton",
            background=[("pressed", "#e6e8ec"), ("active", "#eceef2"), ("!disabled", "#f4f5f7")],
            foreground=[("!disabled", COLOR_INK)],
        )
        style.configure(
            "Play.TButton",
            background="#1f8a4c",
            foreground="#ffffff",
            font=self.panel_small,
            padding=(0, 3),
            borderwidth=0,
            relief="flat",
            focuscolor="#1f8a4c",
        )
        style.map(
            "Play.TButton",
            background=[("pressed", "#176b3b"), ("active", "#187a42"), ("!disabled", "#1f8a4c")],
            foreground=[("!disabled", "#ffffff")],
        )
        style.configure(
            "Horizontal.TScale",
            background=COLOR_CARD,
            troughcolor="#e3e7ef",
        )
        style.configure(
            "Vertical.TScrollbar",
            background=COLOR_CARD,
            troughcolor=COLOR_BG,
            bordercolor=COLOR_BG,
            arrowcolor=COLOR_MUTED,
        )
        style.configure(
            "Horizontal.TScrollbar",
            background=COLOR_CARD,
            troughcolor=COLOR_BG,
            bordercolor=COLOR_BG,
            arrowcolor=COLOR_MUTED,
        )
        style.configure(
            "Steps.Treeview",
            font=self.log_font,
            rowheight=24,
            background=COLOR_CARD,
            fieldbackground=COLOR_CARD,
            foreground=COLOR_INK,
            borderwidth=0,
        )
        style.configure(
            "Steps.Treeview.Heading",
            font=self.log_font_bold,
            background="#f3f5f9",
            foreground=COLOR_INK,
            relief="flat",
            padding=(6, 4),
        )
        style.map(
            "Steps.Treeview",
            background=[("selected", COLOR_CARD)],
            foreground=[("selected", COLOR_INK)],
        )

    def _flat_button(self, parent, text, command, kind="secondary"):
        style_name = "Emphasis.TButton" if kind == "primary" else "Quiet.TButton"
        return ttk.Button(parent, text=text, command=command, style=style_name)

    def _paint_mode(self):
        selected = self.mode.get()
        for value, button in self.mode_buttons.items():
            style_name = "ModeOn.TButton" if value == selected else "ModeOff.TButton"
            button.configure(style=style_name)

    def _field(self, parent, label, variable, low, high, width):
        group = tk.Frame(parent, bg=COLOR_CARD)
        tk.Label(
            group, text=label, bg=COLOR_CARD, fg=COLOR_INK, font=self.panel_small,
        ).pack(anchor="w")
        ttk.Spinbox(
            group, from_=low, to=high, width=width, textvariable=variable,
        ).pack(anchor="w", pady=(2, 0))
        return group

    def _chip(self, parent):
        frame = tk.Frame(parent, bg=COLOR_CHIP, padx=10, pady=5)
        label = tk.Label(frame, text="", bg=COLOR_CHIP, fg=COLOR_TEXT, font=self.ui_font_bold)
        label.pack()
        return frame, label

    def _set_chip(self, frame, label, text, fg, flash=False):
        bg = COLOR_CHIP_FLASH if flash else COLOR_CHIP
        frame.configure(bg=bg)
        label.configure(text=text, fg=fg, bg=bg)

    def _build_controls(self):
        shell = tk.Frame(self.win, bg=COLOR_BG)
        shell.pack(side=tk.TOP, fill=tk.X, padx=16, pady=(14, 0))
        card = tk.Frame(shell, bg=COLOR_CARD, padx=12, pady=8)
        card.pack(fill=tk.X)

        top = tk.Frame(card, bg=COLOR_CARD)
        top.pack(fill=tk.X)
        top.columnconfigure(0, weight=1)

        mode_row = tk.Frame(top, bg=COLOR_CARD)
        mode_row.grid(row=0, column=0, sticky="w")
        self.mode_buttons = {}
        for value, label in (("minimax", "Minimax"), ("alphabeta", "Alpha-Beta")):
            button = ttk.Button(
                mode_row, text=label, style="ModeOff.TButton", width=11,
                command=lambda value=value: self.mode.set(value),
            )
            button.pack(side=tk.LEFT)
            self.mode_buttons[value] = button
        self._paint_mode()

        actions = tk.Frame(top, bg=COLOR_CARD)
        actions.grid(row=0, column=1, sticky="e")
        ttk.Button(
            actions, text="New", command=self.new_tree, style="New.TButton", width=5,
        ).pack(side=tk.LEFT, padx=(0, 8))
        ttk.Button(
            actions, text="Run", command=self.run_algorithm, style="Run.TButton", width=5,
        ).pack(side=tk.LEFT)

        play = tk.Frame(top, bg=COLOR_CARD)
        play.grid(row=1, column=0, sticky="sw", pady=(10, 0))
        self.play_btn = ttk.Button(
            play, text="▶ Play", command=self.toggle_play, style="Play.TButton", width=8,
        )
        self.play_btn.pack(side=tk.LEFT)
        ttk.Button(
            play, text="◀ Prev", command=self.prev_step, style="Arrow.TButton", width=8,
        ).pack(side=tk.LEFT, padx=(6, 0))
        ttk.Button(
            play, text="Next ▶", command=self.next_step, style="Arrow.TButton", width=8,
        ).pack(side=tk.LEFT, padx=(4, 0))

        tk.Label(
            play, text="Speed", bg=COLOR_CARD, fg=COLOR_INK, font=self.panel_small,
        ).pack(side=tk.LEFT, padx=(14, 6))
        ttk.Scale(
            play, from_=1, to=10, orient=tk.HORIZONTAL, length=110,
            variable=self.speed_var,
        ).pack(side=tk.LEFT)

        fields = tk.Frame(top, bg=COLOR_CARD)
        fields.grid(row=1, column=1, sticky="e", pady=(10, 0))
        self._field(fields, "Depth", self.depth_var, DEPTH_MIN, DEPTH_MAX, 4).pack(
            side=tk.LEFT, padx=(0, 12),
        )
        self._field(fields, "Branching", self.branch_var, BRANCH_MIN, BRANCH_MAX, 4).pack(
            side=tk.LEFT, padx=(0, 12),
        )
        self._field(fields, "Leaf min", self.leaf_min_var, -LEAF_BOUND, LEAF_BOUND, 6).pack(
            side=tk.LEFT, padx=(0, 12),
        )
        self._field(fields, "Leaf max", self.leaf_max_var, -LEAF_BOUND, LEAF_BOUND, 6).pack(
            side=tk.LEFT,
        )

    def _build_status(self):
        status = tk.Frame(self.win, bg=COLOR_BG)
        status.pack(side=tk.TOP, fill=tk.X, padx=16, pady=(10, 0))
        tk.Label(
            status, text="Current Move:", bg=COLOR_BG, fg=COLOR_INK,
            font=self.ui_font_bold,
        ).pack(side=tk.LEFT)
        self.event_label = tk.Label(
            status, text=self.current_label, bg=COLOR_BG, fg=COLOR_INK,
            anchor="w", font=self.ui_font,
        )
        self.event_label.pack(side=tk.LEFT, fill=tk.X, expand=True, padx=(8, 0))
        self.step_chip, self.step_label = self._chip(status)
        self.alpha_chip, self.alpha_label = self._chip(status)
        self.beta_chip, self.beta_label = self._chip(status)
        self.value_chip, self.value_label = self._chip(status)
        self.prune_chip, self.prune_label = self._chip(status)
        for chip in (
            self.prune_chip, self.value_chip, self.beta_chip, self.alpha_chip, self.step_chip,
        ):
            chip.pack(side=tk.RIGHT, padx=(8, 0))

    def _build_canvas(self):
        body = tk.Frame(self.win, bg=COLOR_BG)
        body.pack(side=tk.TOP, fill=tk.BOTH, expand=True, padx=16, pady=12)
        self.pane = ttk.Panedwindow(body, orient=tk.HORIZONTAL)
        self.pane.pack(fill=tk.BOTH, expand=True)
        self._sash_placed = False

        canvas_border = tk.Frame(self.pane, bg=COLOR_LINE, padx=1, pady=1)
        canvas_wrap = tk.Frame(canvas_border, bg=COLOR_CANVAS)
        canvas_wrap.pack(fill=tk.BOTH, expand=True)
        self.canvas = tk.Canvas(
            canvas_wrap, background=COLOR_CANVAS, highlightthickness=0, bd=0,
        )
        hbar = ttk.Scrollbar(canvas_wrap, orient=tk.HORIZONTAL, command=self.canvas.xview)
        vbar = ttk.Scrollbar(canvas_wrap, orient=tk.VERTICAL, command=self.canvas.yview)
        self.canvas.configure(xscrollcommand=hbar.set, yscrollcommand=vbar.set)
        self.canvas.grid(row=0, column=0, sticky="nsew")
        vbar.grid(row=0, column=1, sticky="ns")
        hbar.grid(row=1, column=0, sticky="ew")
        canvas_wrap.rowconfigure(0, weight=1)
        canvas_wrap.columnconfigure(0, weight=1)
        self.canvas.bind("<Configure>", self._on_canvas_configure)
        legend = tk.Frame(canvas_wrap, bg=COLOR_CANVAS)
        for color, text in (
            (COLOR_MAX_INK, "MAX"),
            (COLOR_MIN_INK, "MIN"),
            ("#d9a21b", "Current"),
        ):
            tk.Label(legend, text="●", bg=COLOR_CANVAS, fg=color, font=self.panel_font).pack(side=tk.LEFT)
            tk.Label(
                legend, text=text, bg=COLOR_CANVAS, fg=COLOR_INK, font=self.panel_small,
            ).pack(side=tk.LEFT, padx=(2, 10))
        legend.place(x=14, y=12)
        legend.lift()

        log_border = tk.Frame(self.pane, bg=COLOR_LINE)
        self.log = ttk.Treeview(
            log_border, columns=("step", "alpha", "beta"), show="headings",
            style="Steps.Treeview", selectmode="none",
        )
        self.log.heading("step", text="Step", anchor="w")
        self.log.heading("alpha", text="α", anchor="e")
        self.log.heading("beta", text="β", anchor="e")
        self.log.column("step", anchor="w", stretch=True, width=180, minwidth=48)
        self.log.column("alpha", anchor="e", stretch=False, width=76, minwidth=76)
        self.log.column("beta", anchor="e", stretch=False, width=84, minwidth=84)
        self.log.tag_configure("max", background=COLOR_MAX, foreground=COLOR_MAX_INK)
        self.log.tag_configure("min", background=COLOR_MIN, foreground=COLOR_MIN_INK)
        self.log.tag_configure("current-max", background=COLOR_MAX_DEEP, foreground=COLOR_MAX_INK)
        self.log.tag_configure("current-min", background=COLOR_MIN_DEEP, foreground=COLOR_MIN_INK)
        log_scroll = ttk.Scrollbar(log_border, orient=tk.VERTICAL, command=self.log.yview)
        self.log.configure(yscrollcommand=log_scroll.set)
        self.log.grid(row=0, column=0, sticky="nsew")
        log_scroll.grid(row=0, column=1, sticky="ns")
        log_border.rowconfigure(0, weight=1)
        log_border.columnconfigure(0, weight=1)
        self.log.bind("<Configure>", self._sync_step_columns)
        self.pane.add(canvas_border, weight=3)
        self.pane.add(log_border, weight=2)
        self.win.bind("<Map>", self._place_sash, add="+")

    def _read_settings(self):
        try:
            depth = int(self.depth_var.get())
            branching = int(self.branch_var.get())
            leaf_min = int(self.leaf_min_var.get())
            leaf_max = int(self.leaf_max_var.get())
        except (tk.TclError, ValueError):
            messagebox.showerror("Invalid input", "Depth, branching, and leaf bounds must be integers.")
            return None
        if not DEPTH_MIN <= depth <= DEPTH_MAX:
            messagebox.showerror("Invalid depth", f"Depth must be {DEPTH_MIN}–{DEPTH_MAX}.")
            return None
        if not BRANCH_MIN <= branching <= BRANCH_MAX:
            messagebox.showerror(
                "Invalid branching",
                f"Branching factor must be {BRANCH_MIN}–{BRANCH_MAX}.",
            )
            return None
        if not -LEAF_BOUND <= leaf_min <= LEAF_BOUND or not -LEAF_BOUND <= leaf_max <= LEAF_BOUND:
            messagebox.showerror(
                "Invalid leaf range",
                f"Leaf bounds must be between −{LEAF_BOUND} and {LEAF_BOUND}.",
            )
            return None
        if leaf_min > leaf_max:
            leaf_min, leaf_max = leaf_max, leaf_min
            self.leaf_min_var.set(leaf_min)
            self.leaf_max_var.set(leaf_max)
        return depth, branching, leaf_min, leaf_max

    def _stop_playback(self):
        self.playing = False
        self.play_btn.configure(text="▶ Play")
        if self.after_id is not None:
            self.win.after_cancel(self.after_id)
            self.after_id = None

    def new_tree(self):
        settings = self._read_settings()
        if settings is None:
            return
        self._stop_playback()
        depth, branching, leaf_min, leaf_max = settings
        self.root = build_tree(depth, branching, leaf_min, leaf_max)
        self.events = []
        self.step = -1
        self.current_label = (
            f"New tree: depth {depth}, branching {branching}, "
            f"leaves in [{leaf_min}, {leaf_max}]. Click Run."
        )
        self._reset_visual()
        self._refresh()

    def run_algorithm(self):
        if self.root is None:
            self.new_tree()
            if self.root is None:
                return
        self._stop_playback()
        self._reset_visual()
        self.events = []
        if self.mode.get() == "minimax":
            minimax_record(self.root, self.events)
            self.current_label = f"Minimax recorded {len(self.events)} steps. Press Next or Play."
        else:
            alphabeta_record(self.root, -math.inf, math.inf, self.events)
            self.current_label = (
                f"Alpha-beta recorded {len(self.events)} steps. Press Next or Play."
            )
        self.step = -1
        self._refresh()

    def _reset_visual(self):
        self.alpha = None
        self.beta = None
        self.flash = None
        self.prune_count = 0
        self.active_node = None
        if self.root is None:
            return
        stack = [self.root]
        while stack:
            node = stack.pop()
            node.visited = False
            node.pruned = False
            node.prune_root = False
            node.active = False
            node.shown_value = node.value if node.is_leaf else None
            stack.extend(node.children)

    def _mark_pruned(self, node, is_root=True):
        node.pruned = True
        node.prune_root = is_root
        for child in node.children:
            self._mark_pruned(child, False)

    def _focus(self, node):
        if self.active_node is not None and self.active_node is not node:
            self.active_node.active = False
        node.active = True
        self.active_node = node

    def _apply(self, event):
        node = event["node"]
        kind = event["type"]
        if "alpha" in event:
            self.alpha = event["alpha"]
            self.beta = event["beta"]
        self.flash = event.get("which")
        self.current_label = event["label"]
        self._focus(node)

        if kind == "leaf":
            node.visited = True
            node.shown_value = event["value"]
        elif kind == "update" and event.get("which") == "value":
            node.visited = True
            node.shown_value = event["value"]
        elif kind == "prune":
            self._mark_pruned(node)
            self.prune_count += 1
        elif kind == "exit":
            node.visited = True
            node.shown_value = event["value"]

    def show_step(self, index):
        self.step = index
        self._reset_visual()
        if index >= 0:
            for event in self.events[:index + 1]:
                self._apply(event)
        self._refresh()

    def next_step(self):
        if not self.events:
            self.current_label = "Click Run before stepping."
            self._refresh_status()
            return
        if self.step >= len(self.events) - 1:
            self._stop_playback()
            return
        self.step += 1
        self.show_step(self.step)

    def prev_step(self):
        if not self.events:
            self.current_label = "Click Run before stepping."
            self._refresh_status()
            return
        self._stop_playback()
        if self.step < 0:
            return
        self.step -= 1
        if self.step < 0:
            self._reset_visual()
            self.current_label = "Back to the start. Press Next or Play."
            self._refresh()
            return
        self.show_step(self.step)

    def toggle_play(self):
        if self.playing:
            self._stop_playback()
            return
        if not self.events:
            self.run_algorithm()
            if not self.events:
                return
        if self.step >= len(self.events) - 1:
            self.step = -1
            self.show_step(self.step)
        self.playing = True
        self.play_btn.configure(text="❚❚ Pause")
        self._tick()

    def _delay_ms(self):
        speed = max(1, min(10, int(self.speed_var.get())))
        return int(1200 - (speed - 1) * (1100 / 9))

    def _tick(self):
        self.after_id = None
        if not self.playing:
            return
        if self.step >= len(self.events) - 1:
            self._stop_playback()
            return
        self.step += 1
        self.show_step(self.step)
        self.after_id = self.win.after(self._delay_ms(), self._tick)

    def _refresh(self):
        self._draw()
        self._refresh_status()
        self._refresh_log()

    def _refresh_status(self):
        total = len(self.events)
        if total == 0:
            self.step_label.configure(text="Step — / —")
        else:
            shown = 0 if self.step < 0 else self.step + 1
            self.step_label.configure(text=f"Step {shown} / {total}")
        self.event_label.configure(text=self.current_label)

        ab = self.mode.get() == "alphabeta" and self.events
        if ab and self.step >= 0:
            alpha_text, beta_text = f"α  {fmt(self.alpha)}", f"β  {fmt(self.beta)}"
            alpha_color = COLOR_FLASH if self.flash == "alpha" else COLOR_MAX_INK
            beta_color = COLOR_FLASH if self.flash == "beta" else COLOR_MIN_INK
        elif ab:
            alpha_text, beta_text = "α  −∞", "β  +∞"
            alpha_color = beta_color = COLOR_MUTED
        else:
            alpha_text, beta_text = "α  n/a", "β  n/a"
            alpha_color = beta_color = COLOR_MUTED
        self._set_chip(self.alpha_chip, self.alpha_label, alpha_text, alpha_color, self.flash == "alpha")
        self._set_chip(self.beta_chip, self.beta_label, beta_text, beta_color, self.flash == "beta")

        if self.active_node is not None and self.active_node.shown_value is not None:
            shown = self.active_node.shown_value
        elif self.step >= 0 and self.events:
            shown = self.events[self.step].get("value")
        else:
            shown = None
        value_color = COLOR_FLASH if self.flash == "value" else COLOR_TEXT
        self._set_chip(
            self.value_chip, self.value_label, f"Value  {fmt(shown)}",
            value_color, self.flash == "value",
        )
        self._set_chip(self.prune_chip, self.prune_label, f"Pruned  {self.prune_count}", COLOR_MUTED)

    def _place_sash(self, _event=None):
        if self._sash_placed:
            return
        width = self.pane.winfo_width()
        if width < 200:
            return
        self._sash_placed = True
        self.pane.sashpos(0, int(width * 0.62))

    def _sync_step_columns(self, _event=None):
        width = self.log.winfo_width()
        if width < 80:
            return
        alpha_w = 76
        beta_w = 84
        step_w = max(48, width - alpha_w - beta_w - 16)
        self.log.column("alpha", width=alpha_w, minwidth=alpha_w, stretch=False)
        self.log.column("beta", width=beta_w, minwidth=beta_w, stretch=False)
        self.log.column("step", width=step_w, minwidth=48, stretch=True)

    def _refresh_log(self):
        self.log.delete(*self.log.get_children())
        if self.step < 0:
            return
        last = None
        for index, event in enumerate(self.events[:self.step + 1]):
            alpha, beta = step_bounds(event)
            kind = "max" if event["node"].is_max else "min"
            if index == self.step:
                kind = f"current-{kind}"
            last = self.log.insert(
                "", "end",
                values=(f"{step_glyph(event)}   {event['label']}", alpha, beta),
                tags=(kind,),
            )
        if last is not None:
            self.log.see(last)
        self._sync_step_columns()

    def _node_fill(self, node):
        if node.active:
            return COLOR_ACTIVE
        if node.pruned and not node.visited:
            return COLOR_PRUNED
        if node.visited:
            return COLOR_MAX if node.is_max else COLOR_MIN
        return COLOR_IDLE

    def _draw_node(self, node):
        r = NODE_R
        fill = self._node_fill(node)
        outline = COLOR_MAX_INK if node.is_max else COLOR_MIN_INK
        width = 2 if node.active else 1
        if node.pruned and not node.active:
            outline = "#b7bcc4"
        shadow = "#e1e5ee"
        if node.is_max:
            self.canvas.create_rectangle(
                node.x - r + 2, node.y - r + 3, node.x + r + 2, node.y + r + 3,
                fill=shadow, outline="",
            )
            self.canvas.create_rectangle(
                node.x - r, node.y - r, node.x + r, node.y + r,
                fill=fill, outline=outline, width=width,
            )
        else:
            self.canvas.create_oval(
                node.x - r + 2, node.y - r + 3, node.x + r + 2, node.y + r + 3,
                fill=shadow, outline="",
            )
            self.canvas.create_oval(
                node.x - r, node.y - r, node.x + r, node.y + r,
                fill=fill, outline=outline, width=width,
            )
        if node.shown_value is None:
            text = "?"
            color = COLOR_MUTED
        elif node.pruned and not node.visited:
            text = fmt(node.shown_value)
            color = COLOR_MUTED
        else:
            text = fmt(node.shown_value)
            color = COLOR_MAX_INK if node.is_max else COLOR_MIN_INK
        value_font = self.node_font_active if node.active else self.node_font
        self.canvas.create_text(
            node.x, node.y, text=text, fill=color, font=value_font,
        )
        if node.prune_root:
            self.canvas.create_text(
                node.x, node.y + r + 11, text="pruned", fill="#8a9098",
                font=self.small_font,
            )

    def _draw_step_badge(self, node):
        if self.step < 0 or not self.events:
            return
        event = self.events[self.step]
        if event["node"] is not node:
            return
        ink = COLOR_MAX_INK if node.is_max else COLOR_MIN_INK
        fill = COLOR_MAX if node.is_max else COLOR_MIN
        radius = 13
        cx = node.x
        cy = node.y - NODE_R - 15
        self.canvas.create_oval(
            cx - radius, cy - radius, cx + radius, cy + radius,
            fill=fill, outline=ink, width=2,
        )
        self.canvas.create_text(
            cx, cy, text=step_glyph(event), fill=ink, font=self.badge_font,
        )

    def _on_canvas_configure(self, event):
        if self._drawing or event.width < 20 or event.height < 20:
            return
        width, height = self._view_size
        if abs(event.width - width) < 20 and abs(event.height - height) < 20:
            return
        self._pending_view = (event.width, event.height)
        if self._configure_after is not None:
            return
        self._configure_after = self.win.after_idle(self._apply_view_size)

    def _apply_view_size(self):
        self._configure_after = None
        size = getattr(self, "_pending_view", None)
        if size is None or size == self._view_size:
            return
        self._view_size = size
        self._draw()

    def _center_tree(self):
        layout_tree(self.root)
        nodes = []
        stack = [self.root]
        while stack:
            node = stack.pop()
            nodes.append(node)
            stack.extend(node.children)
        pad = NODE_R + 36
        min_x = min(node.x for node in nodes) - pad
        max_x = max(node.x for node in nodes) + pad
        min_y = min(node.y for node in nodes) - pad
        max_y = max(node.y for node in nodes) + NODE_R + 24
        tree_w = max_x - min_x
        tree_h = max_y - min_y
        view_w, view_h = self._view_size
        if view_w < 20 or view_h < 20:
            view_w = max(self.canvas.winfo_width(), 1)
            view_h = max(self.canvas.winfo_height(), 1)
        width = max(tree_w, view_w)
        height = max(tree_h, view_h)
        dx = (width - tree_w) / 2 - min_x
        dy = (height - tree_h) / 2 - min_y
        for node in nodes:
            node.x += dx
            node.y += dy
        self.canvas.configure(scrollregion=(0, 0, width, height))
        return width, height, view_w, view_h

    def _draw(self):
        if self._drawing:
            return
        self._drawing = True
        try:
            self._draw_scene()
        finally:
            self._drawing = False

    def _draw_scene(self):
        self.canvas.delete("all")
        if self.root is None:
            return
        width, height, view_w, view_h = self._center_tree()

        def edges(node):
            for child in node.children:
                color = COLOR_EDGE_PRUNED if child.pruned else COLOR_EDGE
                dash = (4, 3) if child.pruned else None
                self.canvas.create_line(
                    node.x, node.y, child.x, child.y,
                    fill=color, width=2, dash=dash,
                )
                edges(child)

        def nodes(node):
            self._draw_node(node)
            for child in node.children:
                nodes(child)

        edges(self.root)
        nodes(self.root)
        focus = self.active_node
        if focus is None and self.step >= 0:
            focus = self.events[self.step]["node"]
        if focus is not None:
            self._draw_step_badge(focus)
            self._scroll_to(focus, width, height, view_w, view_h)

    def _scroll_to(self, node, content_w, content_h, view_w, view_h):
        if content_w <= view_w + 2 and content_h <= view_h + 2:
            self.canvas.xview_moveto(0)
            self.canvas.yview_moveto(0)
            return
        span_x = max(1.0, content_w)
        span_y = max(1.0, content_h)
        fx = (node.x - view_w / 2) / span_x
        fy = (node.y - view_h / 2) / span_y
        self.canvas.xview_moveto(min(1.0, max(0.0, fx)))
        self.canvas.yview_moveto(min(1.0, max(0.0, fy)))

    def on_close(self):
        self._stop_playback()
        if self._configure_after is not None:
            self.win.after_cancel(self._configure_after)
            self._configure_after = None
        self.win.destroy()


def main():
    win = tk.Tk()
    VisualizerApp(win)
    win.mainloop()


if __name__ == "__main__":
    main()
