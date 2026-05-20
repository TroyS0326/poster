from __future__ import annotations
import re
from pathlib import Path
from PIL import ImageFont
from reels.design_system import KEYWORD_COLOR_RULES

FONT_DIR   = Path(__file__).parent.parent / "assets" / "fonts"
MONTSERRAT = FONT_DIR / "Montserrat-Variable.ttf"

def load_font(size: int, bold: bool = False, black: bool = False):
    if MONTSERRAT.exists():
        f = ImageFont.truetype(str(MONTSERRAT), size)
        try:
            weight = 900 if black else (800 if bold else 400)
            f.set_variation_by_axes([weight])
        except Exception:
            pass   # variable axis not supported, uses default weight
        return f
    # fallbacks
    name = "Bold" if (bold or black) else "Regular"
    for path in [
        f"/usr/share/fonts/truetype/liberation/LiberationSans-{name}.ttf",
        f"/usr/share/fonts/truetype/dejavu/DejaVuSans{'-Bold' if bold else ''}.ttf",
    ]:
        if Path(path).exists():
            return ImageFont.truetype(path, size)
    return ImageFont.load_default()

def emphasis_color(word: str, palette) -> tuple[int, int, int]:
    token = word.lower().strip(".,!?:;")
    rule  = KEYWORD_COLOR_RULES.get(token)
    if rule == "danger":
        return tuple(int(palette.danger[i:i+2], 16) for i in (1, 3, 5))
    if rule == "accent":
        return tuple(int(palette.accent[i:i+2], 16) for i in (1, 3, 5))
    if rule == "accent_alt":
        return tuple(int(palette.accent_alt[i:i+2], 16) for i in (1, 3, 5))
    return palette.text
