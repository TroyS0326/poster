from __future__ import annotations

from dataclasses import dataclass


@dataclass(frozen=True)
class Palette:
    base_top: str
    base_bottom: str
    accent: str
    accent_alt: str
    danger: str
    text: tuple[int, int, int]


PALETTES: dict[str, Palette] = {
    "xeanvi_dark": Palette("#05070d", "#101b2d", "#1f8fff", "#1dd3b0", "#ef4444", (238, 244, 255)),
    "xeanvi_control": Palette("#070b12", "#122033", "#16a34a", "#2dd4bf", "#f97316", (235, 246, 255)),
}

KEYWORD_COLOR_RULES = {
    "risk": "danger",
    "panic": "danger",
    "discipline": "accent_alt",
    "rules": "accent",
    "setup": "accent",
    "emotion": "danger",
}

LAYOUT_PRESETS = (
    "bold_center_statement",
    "left_text_right_visual",
    "right_text_left_visual",
    "top_statement_bottom_visual",
    "split_panel",
    "hero_visual_with_caption_band",
    "data_overlay_focus",
    "quote_impact",
)


def choose_layout(scene_idx: int, text: str) -> str:
    words = len(text.split())
    if words <= 5:
        return "bold_center_statement"
    if "\n" in text or words > 16:
        return "hero_visual_with_caption_band"
    return LAYOUT_PRESETS[scene_idx % len(LAYOUT_PRESETS)]
