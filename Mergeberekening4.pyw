import tkinter as tk
from tkinter import ttk, messagebox

# =========================
# FESTO PALETTE (zoals jij aanleverde)
# =========================
THEME = {
    "caerul":   "#0091DC",
    "sucaerul": "#C8E6FA",
    "canul":    "#B6BEC6",
    "sucanul":  "#E5E8EB",
    "aterul":   "#000000",
    "white":    "#FFFFFF",
    "muted":    "#4B5563",
    "danger":   "#b00020",
}

HEADER_H = 78

# Track per field whether the current value came from the user or from calculation
SOURCE = {}  # name -> "user" | "calc" | ""

# ---------- Helpers ----------
def parse_float(s: str):
    s = (s or "").strip()
    if not s:
        return None
    return float(s.replace(",", "."))

def fmt_money(x: float):
    return f"{x:.2f}"

def fmt_pct(x: float):
    return f"{x:.2f}"


# ---------- UI field wrapper ----------
class UiField:
    def __init__(
        self,
        parent,
        name: str,
        var: tk.StringVar,
        *,
        readonly=False,
        output_only=False,
        badge_enabled=True,
        badge_text="✓ Calculated",
    ):
        self.name = name
        self.var = var
        self.readonly = readonly
        self.output_only = output_only
        self.badge_enabled = badge_enabled
        self.badge_text = badge_text

        self.box = tk.Frame(
            parent,
            bg=THEME["white"],
            highlightthickness=1,
            highlightbackground=THEME["canul"],
            highlightcolor=THEME["caerul"],
        )

        self.badge = tk.Label(
            self.box,
            text=self.badge_text,
            font=("Segoe UI", 9),
            bg=THEME["white"],
            fg=THEME["muted"],
            padx=8,
        )

        self.entry = tk.Entry(
            self.box,
            textvariable=self.var,
            bd=0,
            relief="flat",
            font=("Segoe UI", 10),
            fg=THEME["aterul"],
            bg=THEME["white"],
            insertbackground=THEME["aterul"],
        )

        self.entry.pack(side="left", fill="both", expand=True, padx=10, pady=8)

        if readonly:
            self.entry.configure(state="readonly", readonlybackground=THEME["white"])

        self.entry.bind("<FocusIn>", lambda _e: self.box.configure(highlightbackground=THEME["caerul"]))
        self.entry.bind("<FocusOut>", lambda _e: self.box.configure(highlightbackground=THEME["canul"]))

        if not readonly:
            self.entry.bind("<KeyRelease>", self._mark_user)

    def _mark_user(self, _e=None):
        # If user clears the field, it's no longer user-provided
        if self.var.get().strip() == "":
            SOURCE[self.name] = ""
        else:
            SOURCE[self.name] = "user"

    def grid(self, **kwargs):
        self.box.grid(**kwargs)

    def set_mode(self, mode: str):
        bg = THEME["sucaerul"] if mode == "output" else THEME["white"]
        self.box.configure(bg=bg)

        if self.readonly:
            self.entry.configure(readonlybackground=bg)
        else:
            self.entry.configure(bg=bg)

        if self.badge_enabled and mode == "output":
            self.badge.configure(bg=bg)
            if not self.badge.winfo_ismapped():
                self.badge.pack(side="right", padx=(0, 6), pady=0)
        else:
            if self.badge.winfo_ismapped():
                self.badge.pack_forget()

    def set_fg(self, color_hex: str):
        self.entry.configure(fg=color_hex)
        if not self.readonly:
            self.entry.configure(insertbackground=color_hex)


# ---------- Gradient ----------
def create_gradient(canvas, width, height, top_hex, bottom_hex):
    def hex_to_rgb(h):
        h = h.lstrip("#")
        return int(h[0:2], 16), int(h[2:4], 16), int(h[4:6], 16)

    r1, g1, b1 = hex_to_rgb(top_hex)
    r2, g2, b2 = hex_to_rgb(bottom_hex)

    denom = max(1, height - 1)
    canvas.delete("gradient")
    for i in range(height):
        t = i / denom
        r = int(r1 + (r2 - r1) * t)
        g = int(g1 + (g2 - g1) * t)
        b = int(b1 + (b2 - b1) * t)
        canvas.create_line(0, i, width, i, fill=f"#{r:02x}{g:02x}{b:02x}", tags=("gradient",))

    # Keep gradient behind everything (header/logo/card)
    canvas.tag_lower("gradient")


# ---------- Status row (auto-hide) plumbing ----------
status_row_index = 10
status_label_widget = None
status_row_visible = [False]

def update_status_visibility():
    if status_label_widget is None:
        return
    has_text = status_var.get().strip() != ""
    if has_text:
        if not status_row_visible[0]:
            status_label_widget.grid(row=status_row_index, column=0, sticky="w", padx=(0, 14), pady=8)
            fields["status"].box.grid(row=status_row_index, column=1, sticky="ew", pady=8)
            status_row_visible[0] = True
    else:
        if status_row_visible[0]:
            status_label_widget.grid_remove()
            fields["status"].box.grid_remove()
            status_row_visible[0] = False


# ---------- Core logic ----------
def set_calc_value(name: str, var: tk.StringVar, value: str):
    var.set(value)
    SOURCE[name] = "calc"

def calculate_all():
    set_calc_value("m_no", margin_no_discount_var, "")
    set_calc_value("m_with", margin_with_discount_var, "")
    set_calc_value("status", status_var, "")

    try:
        C  = parse_float(cost_var.get())
        N1 = parse_float(net1_var.get())
        AV = parse_float(added_value_var.get())
        Dp = parse_float(discount_var.get())
        N2 = parse_float(net2_var.get())
        Mp = parse_float(target_margin_var.get())

        if AV is not None and AV < 0:
            raise ValueError("Added Value cannot be negative.")

        D = None if Dp is None else (Dp / 100.0)
        M = None if Mp is None else (Mp / 100.0)

        discount_assumed = False
        discount_solved = False
        av_assumed_zero = False

        if D is not None and (D < 0 or D > 1):
            raise ValueError("Discount must be between 0% and 100%.")
        if M is not None and (M < 0 or M > 1):
            raise ValueError("Target margin must be between 0% and 100%.")

        # Target margin is on Net2:
        if M is not None and C is not None and N2 is not None:
            messagebox.showwarning(
                "Te veel ingevuld",
                "maak een van de velden leeg om de berekening uit te kunnen voeren"
            )
            return

        # Solve:
        # Net2 = (Net1 + AddedValue) * (1 - Discount)
        # AddedValue is ALWAYS part of Net2 BEFORE discount.
        for _ in range(30):
            progress = False

            # If Net1 + Net2 are given, AV blank, and Discount blank -> assume AV=0 to try solving
            if AV is None and N1 is not None and N2 is not None and D is None:
                AV = 0.0
                av_assumed_zero = True
                progress = True

            # Target margin on Net2
            if M is not None:
                if N2 is None and C is not None:
                    if (1.0 - M) == 0:
                        raise ValueError("Target margin cannot be 100% when solving Net2.")
                    N2 = C / (1.0 - M)
                    progress = True
                if C is None and N2 is not None:
                    C = N2 * (1.0 - M)
                    progress = True

            # Solve discount if possible
            if D is None and (N2 is not None) and (N1 is not None) and (AV is not None):
                denom = (N1 + AV)
                if denom == 0:
                    raise ValueError("Net1 + Added Value cannot be 0 when solving discount.")

                D_candidate = 1.0 - (N2 / denom)

                # If discount would be negative and AV was only assumed (blank field),
                # then set discount to 0% and solve Added Value = Net2 - Net1 (>= 0).
                if D_candidate < 0 and av_assumed_zero and SOURCE.get("added_value", "") != "user":
                    D = 0.0
                    discount_solved = True
                    AV_candidate = N2 - N1
                    if AV_candidate < 0:
                        raise ValueError("Added Value cannot be negative with these inputs.")
                    AV = AV_candidate
                    progress = True
                else:
                    D = D_candidate
                    if D < 0 or D > 1:
                        raise ValueError("Solved discount is outside 0%..100%. Check inputs.")
                    discount_solved = True
                    progress = True

            # Price/discount relations
            if N2 is None and (N1 is not None) and (AV is not None) and (D is not None):
                N2 = (N1 + AV) * (1.0 - D)
                progress = True

            if N1 is None and (N2 is not None) and (AV is not None) and (D is not None):
                if (1.0 - D) == 0:
                    raise ValueError("Discount cannot be 100% when solving Net1 from Net2.")
                N1 = (N2 / (1.0 - D)) - AV
                progress = True

            # If AV is derived, enforce non-negative rule
            if AV is None and (N2 is not None) and (N1 is not None) and (D is not None):
                if (1.0 - D) == 0:
                    raise ValueError("Discount cannot be 100% when solving Added Value.")
                AV_candidate = (N2 / (1.0 - D)) - N1
                if AV_candidate < 0:
                    raise ValueError("Added Value cannot be negative with these inputs.")
                AV = AV_candidate
                progress = True

            # Assume 0% discount if blank AND needed to proceed
            if D is None and Dp is None:
                if (N2 is None and N1 is not None and AV is not None) or \
                   (N1 is None and N2 is not None and AV is not None) or \
                   (AV is None and N2 is not None and N1 is not None):
                    D = 0.0
                    discount_assumed = True
                    progress = True

            if not progress:
                break

        # Write back values (mark calc where applicable)
        if C is not None:
            if SOURCE.get("cost", "") == "user":
                cost_var.set(fmt_money(C))
            else:
                set_calc_value("cost", cost_var, fmt_money(C))

        if N1 is not None:
            if SOURCE.get("net1", "") == "user":
                net1_var.set(fmt_money(N1))
            else:
                set_calc_value("net1", net1_var, fmt_money(N1))

        if AV is not None:
            if AV < 0:
                raise ValueError("Added Value cannot be negative.")
            if SOURCE.get("added_value", "") == "user":
                added_value_var.set(fmt_money(AV))
            else:
                set_calc_value("added_value", added_value_var, fmt_money(AV))

        if D is not None and (Dp is not None or discount_assumed or discount_solved):
            if SOURCE.get("discount", "") == "user":
                discount_var.set(fmt_pct(D * 100.0))
            else:
                set_calc_value("discount", discount_var, fmt_pct(D * 100.0))

        if N2 is not None:
            if SOURCE.get("net2", "") == "user":
                net2_var.set(fmt_money(N2))
            else:
                set_calc_value("net2", net2_var, fmt_money(N2))

        # Margins (output fields)
        if C is not None and N1 is not None and N1 != 0:
            m1 = ((N1 - C) / N1) * 100.0
            set_calc_value("m_no", margin_no_discount_var, fmt_pct(m1))
        else:
            set_calc_value("m_no", margin_no_discount_var, "—")

        if C is not None and N2 is not None and N2 != 0:
            m2 = ((N2 - C) / N2) * 100.0
            set_calc_value("m_with", margin_with_discount_var, fmt_pct(m2))
        else:
            set_calc_value("m_with", margin_with_discount_var, "—")

        set_calc_value("status", status_var, "")

    except ValueError as e:
        set_calc_value("status", status_var, str(e))

    # Apply coloring + badges
    for name, field in fields.items():
        if field.output_only:
            field.set_mode("output")
            continue
        src = SOURCE.get(name, "")
        field.set_mode("output" if src == "calc" else "input")

    fields["status"].set_fg(THEME["danger"] if status_var.get().strip() else THEME["muted"])
    update_status_visibility()


def reset_form():
    for name, var in vars_map.items():
        var.set("")
        SOURCE[name] = ""
    for name, field in fields.items():
        field.set_mode("output" if field.output_only else "input")
        field.set_fg(THEME["aterul"] if name != "status" else THEME["muted"])
    update_status_visibility()


# ---------- Window ----------
window = tk.Tk()
window.title("Margin Calculator by Bart van Let, 2024")
window.geometry("760x880")
window.minsize(640, 760)

style = ttk.Style()
try:
    style.theme_use("clam")
except tk.TclError:
    pass

style.configure("Accent.TButton", background=THEME["caerul"], foreground="#ffffff", padding=(16, 11), borderwidth=0)
style.map("Accent.TButton", background=[("active", THEME["caerul"]), ("pressed", THEME["caerul"])])
style.configure("Ghost.TButton", background=THEME["white"], foreground=THEME["caerul"], padding=(16, 11), borderwidth=1, relief="solid")
style.map("Ghost.TButton", background=[("active", THEME["sucanul"]), ("pressed", THEME["sucanul"])])

canvas = tk.Canvas(window, highlightthickness=0, bd=0)
canvas.pack(fill="both", expand=True)

# Header
header_rect = canvas.create_rectangle(0, 0, 760, HEADER_H, fill=THEME["caerul"], outline="")
header_line = canvas.create_line(0, HEADER_H, 760, HEADER_H, fill=THEME["canul"])
title_text = canvas.create_text(24, HEADER_H / 2, anchor="w",
                               text="Margin Calculator",
                               fill="#ffffff",
                               font=("Segoe UI", 18, "bold"))

# -------- Logo with contrast badge (white) --------
logo = None
logo_id = None
logo_bg_id = None
logo_shadow_id = None

try:
    logo = tk.PhotoImage(file="festo_logo.png")
    logo_shadow_id = canvas.create_rectangle(0, 0, 0, 0, fill=THEME["sucanul"], outline="")
    logo_bg_id = canvas.create_rectangle(0, 0, 0, 0, fill=THEME["white"], outline=THEME["canul"], width=1)
    logo_id = canvas.create_image(0, 0, anchor="e", image=logo)
    canvas.tag_raise(logo_id)
except tk.TclError:
    logo = None
    logo_id = None
# -----------------------------------------------

# Card
card = tk.Frame(canvas, bg=THEME["white"], highlightbackground=THEME["canul"], highlightthickness=1)
inner = tk.Frame(card, bg=THEME["white"])
inner.pack(fill="both", expand=True, padx=26, pady=22)
inner.grid_columnconfigure(1, weight=1)

# Card header
tk.Label(inner, text="Pricing & Margin", bg=THEME["white"], fg=THEME["aterul"],
         font=("Segoe UI", 18, "bold")).grid(row=0, column=0, columnspan=2, sticky="w", pady=(0, 6))

tk.Label(
    inner,
    text=(
        "Hint: Target Margin is on Net2. Added Value is part of Net2 BEFORE discount.\n"
        "Added Value cannot be negative.\n"
        "Color meaning: white fields are your input; light-blue fields are calculated results (✓)."
    ),
    bg=THEME["white"],
    fg=THEME["muted"],
    font=("Segoe UI", 10),
    justify="left",
).grid(row=1, column=0, columnspan=2, sticky="w", pady=(0, 18))

# Variables
cost_var = tk.StringVar()
net1_var = tk.StringVar()
added_value_var = tk.StringVar()
discount_var = tk.StringVar()
net2_var = tk.StringVar()
target_margin_var = tk.StringVar()

margin_no_discount_var = tk.StringVar()
margin_with_discount_var = tk.StringVar()
status_var = tk.StringVar()

vars_map = {
    "cost": cost_var,
    "net1": net1_var,
    "added_value": added_value_var,
    "discount": discount_var,
    "net2": net2_var,
    "target_margin": target_margin_var,
    "m_no": margin_no_discount_var,
    "m_with": margin_with_discount_var,
    "status": status_var,
}

for k in vars_map:
    SOURCE[k] = ""

fields = {}

def add_row(r, label_text, var, name, *, readonly=False, output_only=False, badge_enabled=True):
    lbl = tk.Label(
        inner,
        text=label_text,
        bg=THEME["white"],
        fg=THEME["aterul"],
        font=("Segoe UI", 10, "bold"),
    )
    lbl.grid(row=r, column=0, sticky="w", padx=(0, 14), pady=8)

    f = UiField(
        inner,
        name,
        var,
        readonly=readonly,
        output_only=output_only,
        badge_enabled=badge_enabled,
    )
    f.grid(row=r, column=1, sticky="ew", pady=8)
    fields[name] = f
    return lbl, f

# Inputs
add_row(2, "Cost Price (€):", cost_var, "cost")
add_row(3, "Net1 (Sales Price) (€):", net1_var, "net1")
add_row(4, "Added Value (€):", added_value_var, "added_value")
add_row(5, "Discount Percentage (%):", discount_var, "discount")
add_row(6, "Net2 (Final Sales Price) (€):", net2_var, "net2")
add_row(7, "Target Margin on Net2 (%):", target_margin_var, "target_margin")

# Outputs
add_row(8, "Margin without Discount (%):", margin_no_discount_var, "m_no", readonly=True, output_only=True)
add_row(9, "Margin with Discount & Added Value (%):", margin_with_discount_var, "m_with", readonly=True, output_only=True)

# Status row (auto-hidden)
status_row_index = 10
status_label_widget, _ = add_row(
    status_row_index,
    "Status:",
    status_var,
    "status",
    readonly=True,
    output_only=True,
    badge_enabled=False
)
fields["status"].set_fg(THEME["muted"])
status_row_visible = [True]

# Buttons at bottom
btns = tk.Frame(inner, bg=THEME["white"])
btns.grid(row=11, column=0, columnspan=2, sticky="w", pady=(18, 0))
ttk.Button(btns, text="Calculate / Solve", command=calculate_all, style="Accent.TButton").pack(side="left")
ttk.Button(btns, text="Reset", command=reset_form, style="Ghost.TButton").pack(side="left", padx=(10, 0))

# Defaults
for name, field in fields.items():
    field.set_mode("output" if field.output_only else "input")
update_status_visibility()

# Responsive layout + gradient + logo badge
def on_canvas_resize(event):
    w, h = event.width, event.height
    create_gradient(canvas, w, h, THEME["sucaerul"], THEME["white"])

    canvas.coords(header_rect, 0, 0, w, HEADER_H)
    canvas.coords(header_line, 0, HEADER_H, w, HEADER_H)
    canvas.coords(title_text, 24, HEADER_H / 2)

    # Logo + contrast badge
    if logo_id is not None:
        pad_right = 24
        cx = w - pad_right
        cy = HEADER_H / 2
        canvas.coords(logo_id, cx, cy)

        lw = logo.width()
        lh = logo.height()
        pad_x = 16
        pad_y = 10

        x1 = cx - lw - pad_x
        y1 = cy - (lh / 2) - pad_y
        x2 = cx + pad_x
        y2 = cy + (lh / 2) + pad_y

        if logo_shadow_id is not None:
            canvas.coords(logo_shadow_id, x1 + 2, y1 + 2, x2 + 2, y2 + 2)
        if logo_bg_id is not None:
            canvas.coords(logo_bg_id, x1, y1, x2, y2)

        if logo_bg_id is not None:
            canvas.tag_raise(logo_bg_id)
        canvas.tag_raise(logo_id)

    margin = 26
    card_x = margin
    card_y = HEADER_H + 26
    card_w = max(560, w - 2 * margin)
    card_h = max(600, h - card_y - margin)
    card.place(x=card_x, y=card_y, width=card_w, height=card_h)

canvas.bind("<Configure>", on_canvas_resize)
window.bind("<Return>", lambda _e: calculate_all())
window.mainloop()
