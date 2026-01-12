from dataclasses import dataclass


@dataclass(frozen=True)
class Theme:
    primary: str = "#2563EB"
    primary_soft: str = "#DBEAFE"
    border: str = "#D7DEE8"
    background: str = "#F5F7FB"
    surface: str = "#FFFFFF"
    surface_alt: str = "#F9FBFF"
    text: str = "#0F172A"
    muted: str = "#64748B"
    danger: str = "#B91C1C"


APP_THEME = Theme()

FONT_BODY = ("Segoe UI", 10)
FONT_BODY_BOLD = ("Segoe UI", 10, "bold")
FONT_HEADING = ("Segoe UI", 18, "bold")
FONT_SUBHEADING = ("Segoe UI", 11)
FONT_SECTION = ("Segoe UI", 11, "bold")
FONT_SMALL = ("Segoe UI", 9)

SPACING_XS = 6
SPACING_SM = 10
SPACING_MD = 16
SPACING_LG = 24
