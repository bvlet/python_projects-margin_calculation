import tkinter as tk
from tkinter import ttk
from typing import Callable

from .theme import APP_THEME, FONT_BODY


class FieldRow:
    def __init__(
        self,
        parent: ttk.Frame,
        *,
        name: str,
        label: str,
        variable: tk.StringVar,
        readonly: bool = False,
        output_only: bool = False,
        badge_text: str = "Calculated",
    ) -> None:
        self.name = name
        self.variable = variable
        self.output_only = output_only
        self.badge_text = badge_text

        self.container = ttk.Frame(parent)
        self.label = ttk.Label(self.container, text=label)
        self.input_frame = tk.Frame(
            self.container,
            bg=APP_THEME.surface,
            highlightthickness=1,
            highlightbackground=APP_THEME.border,
            highlightcolor=APP_THEME.primary,
        )
        self.entry = ttk.Entry(
            self.input_frame,
            textvariable=variable,
            font=FONT_BODY,
        )
        self.badge = ttk.Label(
            self.input_frame,
            text=self.badge_text,
            style="Badge.TLabel",
        )

        self.label.grid(row=0, column=0, sticky="w")
        self.input_frame.grid(row=0, column=1, sticky="ew", padx=(16, 0))
        self.container.grid_columnconfigure(1, weight=1)

        self.entry.pack(side="left", fill="both", expand=True, padx=12, pady=8)

        if readonly:
            self.entry.configure(state="readonly")

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
        self.entry.configure(background=bg)
        if is_output:
            if not self.badge.winfo_ismapped():
                self.badge.pack(side="right", padx=(0, 8), pady=0)
        else:
            if self.badge.winfo_ismapped():
                self.badge.pack_forget()

    def set_foreground(self, color: str) -> None:
        self.entry.configure(foreground=color)

    def bind_on_change(self, callback: Callable[[], None]) -> None:
        def handler(_event=None) -> None:
            callback()

        self.entry.bind("<KeyRelease>", handler)
        self.entry.bind("<FocusOut>", handler)
