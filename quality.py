import re
from prompts import BLOCKED_PHRASES

GENERIC_PHRASES = ["unlock your potential", "take your trading to the next level", "ai trading bot makes money"]
UNSAFE_FINANCIAL_PATTERNS = [
    r"\bthis is financial advice\b",
    r"\bfinancial advice guaranteed\b",
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
    hashtags = re.findall(r"#\w+", caption)
    if len(hashtags) > 7:
        return False, "too many hashtags"
    emojis = re.findall(r"[\U0001F300-\U0001FAFF]", caption)
    if len(emojis) > 2:
        return False, "too many emojis"
    return True, "ok"


def validate_image_prompt(prompt: str) -> tuple[bool, str]:
    if not prompt or len(prompt.strip()) < 40:
        return False, "image prompt too short"
    if _contains_blocked(prompt):
        return False, "image prompt contains blocked phrase"
    return True, "ok"
