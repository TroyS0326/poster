from __future__ import annotations

from pathlib import Path
from PIL import ImageFont

from reels.design_system import KEYWORD_COLOR_RULES


def load_font(size: int, bold: bool = False):
    candidates = [
        "/usr/share/fonts/truetype/dejavu/DejaVuSans-Bold.ttf" if bold else "/usr/share/fonts/truetype/dejavu/DejaVuSans.ttf",
        "/usr/share/fonts/truetype/liberation/LiberationSans-Bold.ttf" if bold else "/usr/share/fonts/truetype/liberation/LiberationSans-Regular.ttf",
    ]
    for path in candidates:
        if Path(path).exists():
            return ImageFont.truetype(path, size)
    return ImageFont.load_default()


def emphasis_color(word: str, palette) -> tuple[int, int, int]:
    token = word.lower().strip(".,!?:;")
    rule = KEYWORD_COLOR_RULES.get(token)
    if rule == "danger":
        return tuple(int(palette.danger[i:i+2], 16) for i in (1, 3, 5))
    if rule == "accent":
        return tuple(int(palette.accent[i:i+2], 16) for i in (1, 3, 5))
    if rule == "accent_alt":
        return tuple(int(palette.accent_alt[i:i+2], 16) for i in (1, 3, 5))
    return palette.text
