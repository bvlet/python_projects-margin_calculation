import math
from collections import Counter
import tkinter as tk

from .calculations import calculate_all, reset_values
from .theme import (
    APP_THEME,
    FONT_BODY,
    FONT_HEADING,
    FONT_SECTION,
    FONT_SMALL,
    FONT_SUBHEADING,
    SPACING_LG,
    SPACING_MD,
    SPACING_SM,
    SPACING_XS,
)
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
        self.root.configure(bg=APP_THEME.background)

        self.values, self.sources = reset_values()
        self.variables = {name: tk.StringVar(value=value) for name, value in self.values.items()}

        self.page = tk.Frame(self.root, bg=APP_THEME.background)
        self.page.pack(fill="both", expand=True)

        self.header = tk.Frame(self.page, bg=APP_THEME.background)
        self.header.pack(fill="x", padx=SPACING_LG, pady=(SPACING_LG, SPACING_MD))

        header_left = tk.Frame(self.header, bg=APP_THEME.background)
        header_left.pack(side="left", anchor="w")

        title = tk.Label(header_left, text="Margin Calculator", font=FONT_HEADING, bg=APP_THEME.background)
        subtitle = tk.Label(
            header_left,
            text="Modern pricing and margin analysis toolkit",
            font=FONT_SUBHEADING,
            fg=APP_THEME.muted,
            bg=APP_THEME.background,
        )
        title.pack(anchor="w")
        subtitle.pack(anchor="w", pady=(SPACING_XS, 0))

        self._render_logo()

        self.card = tk.Frame(
            self.page,
            bg=APP_THEME.surface,
            highlightbackground=APP_THEME.border,
            highlightthickness=1,
        )
        self.card.pack(fill="both", expand=True, padx=SPACING_LG, pady=(0, SPACING_LG))

        self.card_inner = tk.Frame(self.card, bg=APP_THEME.surface)
        self.card_inner.pack(fill="both", expand=True, padx=SPACING_LG, pady=SPACING_LG)

        self.form_frame = tk.Frame(self.card_inner, bg=APP_THEME.surface)
        self.form_frame.pack(fill="both", expand=True)
        self.form_frame.grid_columnconfigure(1, weight=1)
        self.label_width = max(len(label) for _, label in FIELD_DEFINITIONS + OUTPUT_DEFINITIONS) + 2

        description = tk.Label(
            self.form_frame,
            text=(
                "Target Margin is calculated on Net2. Added Value is part of Net2 BEFORE discount.\n"
                "Inputs remain white. Calculated fields appear blue with a badge."
            ),
            fg=APP_THEME.muted,
            bg=APP_THEME.surface,
            font=FONT_SMALL,
            justify="left",
            wraplength=640,
        )
        description.grid(row=0, column=0, columnspan=2, sticky="w", pady=(0, SPACING_MD))

        self.fields = {}
        row = 1
        input_width = 220
        row = self._render_section(
            row,
            title="Inputs",
            definitions=FIELD_DEFINITIONS,
            input_width=input_width,
        )

        row = self._render_section(
            row,
            title="Outputs",
            definitions=OUTPUT_DEFINITIONS,
            output_only=True,
            input_width=input_width,
        )

        self.status_field = FieldRow(
            self.form_frame,
            name="status",
            label="Status",
            variable=self.variables["status"],
            readonly=True,
            output_only=True,
            background=APP_THEME.surface,
            label_color=APP_THEME.muted,
            label_width=self.label_width,
            input_width=input_width,
            expand_input=True,
        )
        self.status_field.grid(row=row, column=0, columnspan=2, sticky="ew", pady=(SPACING_MD, 0))
        self.status_field.set_mode("output")
        self.fields["status"] = self.status_field

        self._set_status_style("")

        self.footer_frame = tk.Frame(self.card_inner, bg=APP_THEME.surface)
        self.footer_frame.pack(fill="x", pady=(SPACING_LG, 0))

        self.actions = tk.Frame(self.footer_frame, bg=APP_THEME.surface)
        self.actions.pack(side="left", anchor="w")

        self.calculate_button = tk.Button(
            self.actions,
            text="Calculate",
            command=self.on_calculate,
            font=FONT_BODY,
            bg=APP_THEME.primary,
            fg="#FFFFFF",
            activebackground=APP_THEME.primary,
            activeforeground="#FFFFFF",
            relief="flat",
            bd=0,
            padx=20,
            pady=8,
        )
        self.reset_button = tk.Button(
            self.actions,
            text="Reset",
            command=self.on_reset,
            font=FONT_BODY,
            bg=APP_THEME.surface,
            fg=APP_THEME.primary,
            activebackground=APP_THEME.primary_soft,
            activeforeground=APP_THEME.primary,
            relief="solid",
            bd=1,
            highlightthickness=1,
            highlightbackground=APP_THEME.border,
            padx=20,
            pady=8,
        )

        self.calculate_button.pack(side="left")
        self.reset_button.pack(side="left", padx=(SPACING_SM, 0))

        self.footer = tk.Label(
            self.footer_frame,
            text="© 2026 Bart van Let",
            font=FONT_SMALL,
            fg=APP_THEME.muted,
            bg=APP_THEME.surface,
        )
        self.footer.pack(side="right", anchor="e", padx=(SPACING_MD, 0))

        self.root.bind("<Return>", lambda _event: self.on_calculate())
        self._lock_minimum_size()

    def _render_logo(self) -> None:
        logo = None
        for path in ("festo_logo.png", "png-transparent-festo-hd-logo.png"):
            try:
                logo = tk.PhotoImage(file=path)
                break
            except tk.TclError:
                continue

        if logo is None:
            return

        max_width = 220
        max_height = 56
        scale = max(logo.width() / max_width, logo.height() / max_height)
        if scale > 1:
            factor = math.ceil(scale)
            logo = logo.subsample(factor, factor)

        self._apply_logo_transparency(logo)

        logo_wrap = tk.Frame(self.header, bg=APP_THEME.background)
        logo_wrap.pack(side="right", anchor="e")
        badge = tk.Frame(
            logo_wrap,
            bg=APP_THEME.background,
            highlightthickness=0,
        )
        badge.pack()
        logo_label = tk.Label(badge, image=logo, bg=APP_THEME.background)
        logo_label.image = logo
        logo_label.pack(padx=SPACING_SM, pady=SPACING_XS)

    def _apply_logo_transparency(self, logo: tk.PhotoImage) -> None:
        width = logo.width()
        height = logo.height()
        if width == 0 or height == 0:
            return

        border_colors = []
        for x in range(width):
            border_colors.append(logo.get(x, 0))
            border_colors.append(logo.get(x, height - 1))
        for y in range(height):
            border_colors.append(logo.get(0, y))
            border_colors.append(logo.get(width - 1, y))

        if not border_colors:
            return

        common = Counter(border_colors).most_common(2)
        transparent_colors = {color for color, _count in common}

        for x in range(width):
            for y in range(height):
                if logo.get(x, y) in transparent_colors:
                    logo.transparency_set(x, y, True)

    def _render_section(
        self,
        row: int,
        title: str,
        definitions,
        output_only: bool = False,
        input_width: int = 170,
    ) -> int:
        section_label = tk.Label(
            self.form_frame,
            text=title,
            font=FONT_SECTION,
            bg=APP_THEME.surface,
            fg=APP_THEME.text,
        )
        section_label.grid(row=row, column=0, columnspan=2, sticky="w", pady=(SPACING_SM, SPACING_SM))
        row += 1

        for name, label in definitions:
            field = FieldRow(
                self.form_frame,
                name=name,
                label=label,
                variable=self.variables[name],
                readonly=output_only,
                output_only=output_only,
                background=APP_THEME.surface,
                label_width=self.label_width,
                input_width=input_width,
            )
            field.grid(row=row, column=0, columnspan=2, sticky="ew", pady=SPACING_XS)
            if output_only:
                field.set_mode("output")
            else:
                field.bind_on_change(lambda n=name: self._mark_user(n))
            self.fields[name] = field
            row += 1

        divider = tk.Frame(self.form_frame, bg=APP_THEME.border, height=1)
        divider.grid(row=row, column=0, columnspan=2, sticky="ew", pady=(SPACING_MD, SPACING_MD))
        row += 1
        return row

    def _lock_minimum_size(self) -> None:
        self.root.update_idletasks()
        min_width = self.root.winfo_reqwidth()
        min_height = self.root.winfo_reqheight()
        self.root.minsize(min_width, min_height)
        self.root.geometry(f"{min_width}x{min_height}")

    def _mark_user(self, name: str) -> None:
        value = self.variables[name].get().strip()
        self.sources[name] = "user" if value else ""
        if name == "net1":
            self._sync_net2_from_net1(value)

    def _sync_net2_from_net1(self, net1_value: str) -> None:
        if self.sources.get("net2") == "user":
            return
        if net1_value:
            self.variables["net2"].set(net1_value)
            self.sources["net2"] = "calc"
            self.fields["net2"].set_mode("output")
        else:
            self.variables["net2"].set("")
            self.sources["net2"] = ""
            self.fields["net2"].set_mode("input")

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
