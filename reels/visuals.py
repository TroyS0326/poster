from __future__ import annotations

from dataclasses import dataclass

from reels.compliance import validate_compliance_text

SUPPORTED_VISUAL_STYLES = {
    "fintech_dark",
    "workstation",
    "abstract_risk",
    "market_grid",
    "minimal_gradient",
}

SUPPORTED_VISUAL_BRANDS = {"generic", "xeanvi"}

DEFAULT_VISUAL_STYLE_BY_BRAND = {
    "generic": "minimal_gradient",
    "xeanvi": "fintech_dark",
}

REQUIRED_NEGATIVE_TERMS = [
    "faces",
    "hands",
    "people",
    "cash piles",
    "luxury cars",
    "broker logos",
    "ticker recommendations",
    "profit screenshots",
    "financial advice text",
]

COMMON_NEGATIVE_PROMPT = (
    "no faces, no hands, no people, no cash piles, no luxury cars, "
    "no broker logos, no ticker recommendations, no profit screenshots, no financial advice text"
)


@dataclass(frozen=True)
class VisualPromptPack:
    style: str
    image_prompt: str
    negative_prompt: str
    suggested_background_type: str
    suggested_color: str
    suggested_color_end: str


def resolve_visual_style(brand: str, visual_style: str | None) -> str:
    if brand not in SUPPORTED_VISUAL_BRANDS:
        raise ValueError(f"unsupported brand: {brand}")

    style = (visual_style or "").strip()
    if not style:
        style = DEFAULT_VISUAL_STYLE_BY_BRAND.get(brand, "minimal_gradient")
    if style not in SUPPORTED_VISUAL_STYLES:
        raise ValueError(f"unsupported visual_style: {style}")
    return style


def build_visual_prompt(style: str, brand: str, topic: str) -> VisualPromptPack:
    if brand not in SUPPORTED_VISUAL_BRANDS:
        raise ValueError(f"unsupported brand: {brand}")

    if style not in SUPPORTED_VISUAL_STYLES:
        raise ValueError(f"unsupported visual_style: {style}")

    brand_context = "dark fintech command center" if brand == "xeanvi" else "clean process-first trading workspace"
    prompt_core = {
        "fintech_dark": "dark fintech command center, trading dashboard abstraction, risk-control overlays, checklist UI cards, subtle data glow",
        "workstation": "organized trading workstation desk, multiple neutral analytics monitors, notebook checklist, process-focused setup",
        "abstract_risk": "abstract risk-control composition, layered geometric zones, decision checkpoints, calm and disciplined flow",
        "market_grid": "market scanning grid, dashboard tiles, watchlist matrix abstraction, validation checkpoints, no real symbols",
        "minimal_gradient": "minimal gradient background with subtle grid texture, clean workflow framing, modern disciplined finance aesthetic",
    }[style]

    image_prompt = f"Vertical 9:16 background, {brand_context}, {prompt_core}, topic context: {topic.strip()}, cinematic but clean, no hype."

    validate_compliance_text(image_prompt, "image_prompt")

    negative_prompt = COMMON_NEGATIVE_PROMPT
    for term in REQUIRED_NEGATIVE_TERMS:
        if term not in negative_prompt:
            raise ValueError(f"negative_prompt missing required guidance: {term}")

    palette = {
        "fintech_dark": ("gradient", "#0b1220", "#1e293b"),
        "workstation": ("gradient", "#1f2937", "#374151"),
        "abstract_risk": ("gradient", "#14213d", "#223a5e"),
        "market_grid": ("gradient", "#0f172a", "#134e4a"),
        "minimal_gradient": ("gradient", "#101820", "#1f4068"),
    }[style]

    return VisualPromptPack(
        style=style,
        image_prompt=image_prompt,
        negative_prompt=negative_prompt,
        suggested_background_type=palette[0],
        suggested_color=palette[1],
        suggested_color_end=palette[2],
    )
