"""
Cinematic visual prompts engineered for trading reels that stop scrolls.
Every prompt is designed to feel authentic, not AI-generated.
No humans, no hands, no faces — pure environment storytelling.
"""
from __future__ import annotations
import random

# These are the visual environments that perform best for trading content
CINEMATIC_ENVIRONMENTS = {
    "revenge": [
        "extreme close-up of a trading terminal, red P&L numbers bleeding across the screen, harsh fluorescent light, 3am office darkness, single monitor glow, motion blur on the numbers, no people",
        "abandoned trading desk at night, multiple dark monitors with red candlestick charts, cold blue moonlight through venetian blinds, coffee cup half empty, notebook with crossed-out trade plans, photorealistic, cinematic",
        "macro shot of a keyboard with a single finger hovering over the execute button, red market data reflected in the keys, dramatic side lighting, shallow depth of field, tension implied",
    ],
    "discipline": [
        "clean minimal trading setup at dawn, single ultrawide monitor showing a green P&L dashboard, warm morning light cutting through curtains, organized notebook with written rules visible but unreadable, calm and controlled atmosphere",
        "sleek dark office, teal and blue data visualizations on three monitors, structured checklist UI visible on screen, ambient professional lighting, no clutter, everything deliberate, cinematic vertical shot",
        "close-up of a trading journal, handwritten rules and trade log, pen resting on open page, soft desk lamp, calm focused energy, dark background, professional",
    ],
    "fomo": [
        "fast-moving stock chart on screen, green candle spike happening in real time, blurred background of empty chair as if someone just left, motion blur, urgency in the composition, dramatic lighting",
        "trading terminal screen with a massive green candle appearing, other positions shown in red while one screams higher, the visual tension of missing vs watching, dark moody environment",
    ],
    "system": [
        "overhead drone shot of a minimalist trading desk, single laptop, structured notebook, no extra monitors, clean workspace philosophy, professional morning light, organized intentional layout",
        "close-up of a risk management dashboard, clean UI showing position sizes, loss limits, green system checks, teal accent colors, dark fintech aesthetic, authoritative and controlled",
        "time-lapse style single frame of charts progressing through a trading session, green arrows marking rule-based entries, systematic and methodical, dark background, data visualization art",
    ],
    "truth": [
        "two trading setups side by side, one chaotic with 12 indicators and red P&L, one minimal with clean price action and green P&L, stark visual contrast, documentary style lighting",
        "crumpled paper trading plan on dark desk next to a pristine digital checklist on screen, the story of discipline vs impulse told visually, dramatic directional lighting",
    ],
}

SAFE_SUFFIX = (
    "vertical 9:16 composition, no people, no faces, no hands, no visible text or logos, "
    "no broker interfaces, no profit screenshots, photorealistic cinematic quality, "
    "text-safe composition with clear areas for caption overlay, "
    "shot on RED camera, professional color grade"
)

NEGATIVE = (
    "people, faces, hands, arms, body parts, text, words, letters, logos, "
    "broker platforms, profit screenshots, financial advice, watermarks, "
    "cartoon, illustration, anime, painting, low quality, blurry, "
    "busy background that competes with text overlay"
)


def build_scene_video_prompt(topic: str, scene_text: str) -> str:
    """Generate a cinematic LTX Video prompt for this scene."""
    t = f"{topic} {scene_text}".lower()

    if any(w in t for w in ["revenge", "anger", "frustrat", "blow", "lost", "ruin", "destroy"]):
        pool = CINEMATIC_ENVIRONMENTS["revenge"]
    elif any(w in t for w in ["fomo", "miss", "late", "chasing", "rush"]):
        pool = CINEMATIC_ENVIRONMENTS["fomo"]
    elif any(w in t for w in ["rule", "system", "process", "consistent", "disciplin", "plan"]):
        pool = CINEMATIC_ENVIRONMENTS["discipline"]
    elif any(w in t for w in ["truth", "nobody", "real", "actually", "contrast", "difference"]):
        pool = CINEMATIC_ENVIRONMENTS["truth"]
    else:
        pool = CINEMATIC_ENVIRONMENTS["system"]

    base = random.choice(pool)
    return f"cinematic slow motion video, {base}, {SAFE_SUFFIX}"


def build_image_prompt(topic: str, scene_text: str, scene_index: int, total_scenes: int) -> str:
    """Generate a Stable Diffusion / image gen prompt for static backgrounds."""
    t = f"{topic} {scene_text}".lower()

    if scene_index == 0:
        # Hook scene — most dramatic
        if any(w in t for w in ["revenge", "blow", "lost", "ruin"]):
            env = random.choice(CINEMATIC_ENVIRONMENTS["revenge"])
        else:
            env = random.choice(CINEMATIC_ENVIRONMENTS["truth"])
    elif scene_index == total_scenes - 1:
        # CTA scene — controlled, professional
        env = random.choice(CINEMATIC_ENVIRONMENTS["system"])
    else:
        # Middle scenes — match the emotional arc
        if any(w in t for w in ["rule", "system", "disciplin"]):
            env = random.choice(CINEMATIC_ENVIRONMENTS["discipline"])
        elif any(w in t for w in ["fomo", "miss", "chasing"]):
            env = random.choice(CINEMATIC_ENVIRONMENTS["fomo"])
        else:
            env = random.choice(CINEMATIC_ENVIRONMENTS["system"])

    return (
        f"photorealistic, {env}, {SAFE_SUFFIX}, "
        f"ultra sharp, 8K, professional photography, "
        f"dark moody fintech aesthetic, teal and blue accent lighting"
    )
