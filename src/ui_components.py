import tkinter as tk
from typing import Callable

from .theme import APP_THEME, FONT_BODY, FONT_BODY_BOLD, FONT_SMALL


class FieldRow:
    def __init__(
        self,
        parent: tk.Frame,
        *,
        name: str,
        label: str,
        variable: tk.StringVar,
        readonly: bool = False,
        output_only: bool = False,
        badge_text: str = "Calculated",
        background: str = APP_THEME.surface,
        label_color: str = APP_THEME.text,
        label_width: int = 26,
        input_width: int = 170,
        expand_input: bool = False,
    ) -> None:
        self.name = name
        self.variable = variable
        self.output_only = output_only
        self.badge_text = badge_text
        self.background = background
        self.expand_input = expand_input

        self.container = tk.Frame(parent, bg=background)
        self.label = tk.Label(
            self.container,
            text=label,
            bg=background,
            fg=label_color,
            font=FONT_BODY_BOLD,
            width=label_width,
            anchor="w",
        )
        self.input_frame = tk.Frame(
            self.container,
            bg=APP_THEME.surface,
            highlightthickness=1,
            highlightbackground=APP_THEME.border,
            highlightcolor=APP_THEME.primary,
            width=input_width,
        )
        self.input_frame.grid_propagate(False)
        self.entry = tk.Entry(
            self.input_frame,
            textvariable=variable,
            font=FONT_BODY,
            bd=0,
            relief="flat",
            bg=APP_THEME.surface,
            fg=APP_THEME.text,
            insertbackground=APP_THEME.text,
        )
        self.badge = tk.Label(
            self.input_frame,
            text=self.badge_text,
            bg=APP_THEME.primary_soft,
            fg=APP_THEME.muted,
            font=FONT_SMALL,
            padx=8,
            pady=2,
        )

        self.label.grid(row=0, column=0, sticky="w")
        self.input_frame.grid(
            row=0,
            column=1,
            sticky="ew" if self.expand_input else "e",
            padx=(16, 0),
        )
        if self.expand_input:
            self.container.grid_columnconfigure(0, weight=0)
            self.container.grid_columnconfigure(1, weight=1)
        else:
            self.container.grid_columnconfigure(0, weight=1)
            self.container.grid_columnconfigure(1, weight=0)

        self.entry.pack(side="left", fill="both", expand=True, padx=12, pady=8)

        if readonly:
            self.entry.configure(state="readonly", readonlybackground=APP_THEME.surface)

        self._is_output = False

        self.input_frame.bind("<FocusIn>", lambda _e: self._set_focus(True))
        self.input_frame.bind("<FocusOut>", lambda _e: self._set_focus(False))
        self.entry.bind("<FocusIn>", lambda _e: self._set_focus(True))
        self.entry.bind("<FocusOut>", lambda _e: self._set_focus(False))

    def _set_focus(self, focused: bool) -> None:
        color = APP_THEME.primary if focused else APP_THEME.border
        self.input_frame.configure(highlightbackground=color)

    def grid(self, **kwargs) -> None:
        self.container.grid(**kwargs)

    def set_mode(self, mode: str) -> None:
        is_output = mode == "output"
        if is_output == self._is_output:
            return
        self._is_output = is_output
        bg = APP_THEME.primary_soft if is_output else APP_THEME.surface
        self.input_frame.configure(bg=bg)
        if self.entry.cget("state") == "readonly":
            self.entry.configure(readonlybackground=bg)
        else:
            self.entry.configure(bg=bg)
        if is_output:
            if not self.badge.winfo_ismapped():
                self.badge.place(relx=1.0, rely=0.5, anchor="e", x=-8)
        else:
            if self.badge.winfo_ismapped():
                self.badge.place_forget()

    def set_foreground(self, color: str) -> None:
        self.entry.configure(fg=color, insertbackground=color)

    def bind_on_change(self, callback: Callable[[], None]) -> None:
        def handler(_event=None) -> None:
            callback()

        self.entry.bind("<KeyRelease>", handler)
        self.entry.bind("<FocusOut>", handler)
