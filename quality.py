import re
from prompts import BLOCKED_PHRASES

GENERIC_PHRASES = [
    "unlock your potential",
    "take your trading to the next level",
    "revolutionize your trading",
    "game changer",
    "cutting edge",
    "seamless experience",
    "maximize profits",
    "trade smarter not harder",
    "level up your trading",
    "ai-powered success",
    "dominate the market",
    "financial freedom",
    "passive income",
    "never miss a trade",
    "beat the market",
]

UNSAFE_FINANCIAL_PATTERNS = [
    r"\bthis is financial advice\b",
    r"\bfinancial advice guaranteed\b",
    r"\bguaranteed\b",
    r"\balways\b",
    r"\bnever lose\b",
    r"\brisk-free\b",
    r"\bsure thing\b",
    r"\b100%\b",
    r"\bprofit machine\b",
]

DISCLOSURE = "Not financial advice. Trading involves risk."
SCENE_CUES = [
    "desk", "workstation", "journal", "notebook", "keyboard", "coffee", "monitor", "chair",
    "lab", "sandbox", "studio", "office", "close-up", "over-shoulder", "split scene", "macro",
]
STYLE_CUES = [
    "cinematic", "editorial", "realistic", "isometric", "lighting", "mood", "depth of field",
    "palette", "glow", "contrast", "minimal", "fintech", "vertical", "1080x1350",
]
GENERIC_IMAGE_ONLY = [
    "command center", "dashboard", "dark-mode", "dark mode", "ui panels", "fintech ui",
]


def _contains_blocked(text: str) -> bool:
    lowered = text.lower()
    if any(p in lowered for p in BLOCKED_PHRASES):
        return True
    return any(re.search(pattern, lowered) for pattern in UNSAFE_FINANCIAL_PATTERNS)


def validate_caption(caption: str) -> tuple[bool, str]:
    if not caption or not caption.strip():
        return False, "empty caption"
    if len(caption) < 120 or len(caption) > 1200:
        return False, "caption length out of range"
    if _contains_blocked(caption):
        return False, "caption contains blocked phrase"
    if any(p in caption.lower() for p in GENERIC_PHRASES):
        return False, "caption too generic"

    if caption.count(DISCLOSURE) != 1:
        return False, "caption must include disclosure exactly once"

    hashtags = re.findall(r"#\w+", caption)
    if len(hashtags) > 5:
        return False, "too many hashtags"

    emojis = re.findall(r"[\U0001F300-\U0001FAFF]", caption)
    if len(emojis) > 1:
        return False, "too many emojis"

    return True, "ok"


def validate_image_prompt(prompt: str) -> tuple[bool, str]:
    if not prompt or len(prompt.strip()) < 80:
        return False, "image prompt too short"
    if _contains_blocked(prompt):
        return False, "image prompt contains blocked phrase"

    lowered = prompt.lower()
    has_scene = any(cue in lowered for cue in SCENE_CUES)
    has_style = any(cue in lowered for cue in STYLE_CUES)
    generic_hits = sum(1 for phrase in GENERIC_IMAGE_ONLY if phrase in lowered)

    if not has_scene:
        return False, "image prompt missing scene/environment cue"
    if not has_style:
        return False, "image prompt missing style/camera/mood cue"
    if generic_hits >= 2 and not (has_scene and has_style):
        return False, "image prompt too generic"

    return True, "ok"
