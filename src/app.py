import tkinter as tk
from tkinter import ttk

from .calculations import calculate_all, reset_values
from .theme import APP_THEME, FONT_BODY, FONT_HEADING, FONT_SUBHEADING
from .ui_components import FieldRow


FIELD_DEFINITIONS = (
    ("cost", "Cost Price (€):"),
    ("net1", "Net1 (Sales Price) (€):"),
    ("added_value", "Added Value (€):"),
    ("discount", "Discount Percentage (%):"),
    ("net2", "Net2 (Final Sales Price) (€):"),
    ("target_margin", "Target Margin on Net2 (%):"),
)

OUTPUT_DEFINITIONS = (
    ("m_no", "Margin without Discount (%):"),
    ("m_with", "Margin with Discount & Added Value (%):"),
)


class MarginCalculatorApp:
    def __init__(self, root: tk.Tk) -> None:
        self.root = root
        self.root.title("Margin Calculator")
        self.root.geometry("860x720")
        self.root.minsize(720, 640)
        self.root.configure(bg=APP_THEME.background)

        self.style = ttk.Style()
        self._configure_style()

        self.values, self.sources = reset_values()
        self.variables = {name: tk.StringVar(value=value) for name, value in self.values.items()}

        self.header = ttk.Frame(self.root, padding=(24, 20))
        self.header.pack(fill="x")

        title = ttk.Label(self.header, text="Margin Calculator", font=FONT_HEADING)
        subtitle = ttk.Label(
            self.header,
            text="Calculate cost, pricing, discounts, and margins with clarity.",
            font=FONT_SUBHEADING,
            foreground=APP_THEME.muted,
        )
        title.pack(anchor="w")
        subtitle.pack(anchor="w", pady=(4, 0))

        self._render_logo()

        self.content = ttk.Frame(self.root, padding=(24, 8))
        self.content.pack(fill="both", expand=True)

        self.card = ttk.Frame(self.content, style="Card.TFrame", padding=(24, 20))
        self.card.pack(fill="both", expand=True)

        self.form_frame = ttk.Frame(self.card)
        self.form_frame.pack(fill="both", expand=True)
        self.form_frame.grid_columnconfigure(1, weight=1)

        description = ttk.Label(
            self.form_frame,
            text=(
                "Target Margin is calculated on Net2. Added Value is part of Net2 BEFORE discount.\n"
                "Inputs remain white. Calculated fields appear blue with a badge."
            ),
            foreground=APP_THEME.muted,
            font=FONT_BODY,
        )
        description.grid(row=0, column=0, columnspan=2, sticky="w", pady=(0, 16))

        self.fields = {}
        row = 1
        for name, label in FIELD_DEFINITIONS:
            field = FieldRow(
                self.form_frame,
                name=name,
                label=label,
                variable=self.variables[name],
            )
            field.grid(row=row, column=0, columnspan=2, sticky="ew", pady=6)
            field.bind_on_change(lambda n=name: self._mark_user(n))
            self.fields[name] = field
            row += 1

        separator = ttk.Separator(self.form_frame)
        separator.grid(row=row, column=0, columnspan=2, sticky="ew", pady=(12, 12))
        row += 1

        for name, label in OUTPUT_DEFINITIONS:
            field = FieldRow(
                self.form_frame,
                name=name,
                label=label,
                variable=self.variables[name],
                readonly=True,
                output_only=True,
            )
            field.grid(row=row, column=0, columnspan=2, sticky="ew", pady=6)
            field.set_mode("output")
            self.fields[name] = field
            row += 1

        self.status_field = FieldRow(
            self.form_frame,
            name="status",
            label="Status:",
            variable=self.variables["status"],
            readonly=True,
            output_only=True,
        )
        self.status_field.grid(row=row, column=0, columnspan=2, sticky="ew", pady=(12, 6))
        self.status_field.set_mode("output")
        self.fields["status"] = self.status_field
        row += 1

        self._set_status_style("")

        self.actions = ttk.Frame(self.card)
        self.actions.pack(fill="x", pady=(16, 0))

        self.calculate_button = ttk.Button(
            self.actions,
            text="Calculate",
            command=self.on_calculate,
            style="Primary.TButton",
        )
        self.reset_button = ttk.Button(
            self.actions,
            text="Reset",
            command=self.on_reset,
            style="Ghost.TButton",
        )

        self.calculate_button.pack(side="left")
        self.reset_button.pack(side="left", padx=(12, 0))

        self.root.bind("<Return>", lambda _event: self.on_calculate())

    def _configure_style(self) -> None:
        self.style.theme_use("clam")
        self.style.configure("TLabel", background=APP_THEME.background, font=FONT_BODY, foreground=APP_THEME.text)
        self.style.configure("Card.TFrame", background=APP_THEME.surface, relief="flat")
        self.style.configure(
            "Primary.TButton",
            font=FONT_BODY,
            background=APP_THEME.primary,
            foreground="#FFFFFF",
            padding=(18, 10),
            borderwidth=0,
        )
        self.style.map(
            "Primary.TButton",
            background=[("active", APP_THEME.primary), ("pressed", APP_THEME.primary)],
        )
        self.style.configure(
            "Ghost.TButton",
            font=FONT_BODY,
            background=APP_THEME.surface,
            foreground=APP_THEME.primary,
            padding=(18, 10),
            borderwidth=1,
            relief="solid",
        )
        self.style.map(
            "Ghost.TButton",
            background=[("active", APP_THEME.primary_soft), ("pressed", APP_THEME.primary_soft)],
        )
        self.style.configure(
            "Badge.TLabel",
            background=APP_THEME.primary_soft,
            foreground=APP_THEME.muted,
            font=("Segoe UI", 9, "bold"),
            padding=(8, 2),
        )

    def _render_logo(self) -> None:
        try:
            logo = tk.PhotoImage(file="festo_logo.png")
        except tk.TclError:
            return

        logo_label = ttk.Label(self.header, image=logo, background=APP_THEME.background)
        logo_label.image = logo
        logo_label.pack(anchor="e", side="right")

    def _mark_user(self, name: str) -> None:
        value = self.variables[name].get().strip()
        self.sources[name] = "user" if value else ""

    def _set_status_style(self, status: str) -> None:
        color = APP_THEME.danger if status else APP_THEME.muted
        self.status_field.set_foreground(color)

    def on_calculate(self) -> None:
        for key in self.values:
            self.values[key] = self.variables[key].get()

        result = calculate_all(self.values, self.sources)
        self.values = result.values
        self.sources = result.sources

        for key, value in self.values.items():
            self.variables[key].set(value)

        for name, field in self.fields.items():
            if field.output_only:
                field.set_mode("output")
                continue
            field.set_mode("output" if self.sources.get(name) == "calc" else "input")

        self._set_status_style(self.values.get("status", ""))

    def on_reset(self) -> None:
        self.values, self.sources = reset_values()
        for key, value in self.values.items():
            self.variables[key].set(value)
        for field in self.fields.values():
            field.set_mode("output" if field.output_only else "input")
        self._set_status_style("")


def main() -> None:
    root = tk.Tk()
    MarginCalculatorApp(root)
    root.mainloop()


if __name__ == "__main__":
    main()
