from dataclasses import dataclass


@dataclass(frozen=True)
class Theme:
    primary: str = "#2563EB"
    primary_soft: str = "#DBEAFE"
    border: str = "#D1D5DB"
    background: str = "#F8FAFC"
    surface: str = "#FFFFFF"
    text: str = "#0F172A"
    muted: str = "#64748B"
    danger: str = "#B91C1C"


APP_THEME = Theme()
FONT_BODY = ("Segoe UI", 10)
FONT_HEADING = ("Segoe UI", 16, "bold")
FONT_SUBHEADING = ("Segoe UI", 11)
