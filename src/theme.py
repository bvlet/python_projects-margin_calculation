from dataclasses import dataclass


@dataclass(frozen=True)
class Theme:
    primary: str = "#0091DC"
    primary_soft: str = "#C8E6FA"
    border: str = "#B6BEC6"
    background: str = "#E5E8EB"
    surface: str = "#FFFFFF"
    surface_alt: str = "#C8E6FA"
    text: str = "#000000"
    muted: str = "#717D86"
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
