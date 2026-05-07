import re

from prompts import BLOCKED_PHRASES

DISCLOSURE = "Not financial advice. Trading involves risk."
ALLOWED_DISCLOSURE_LOWER = DISCLOSURE.lower()

GENERIC_PHRASES = [
    "unlock your potential",
    "take your trading to the next level",
    "revolutionize your trading",
    "game changer",
    "cutting edge",
    "seamless experience",
    "trade smarter not harder",
    "level up your trading",
    "ai-powered success",
    "never miss a trade",
]

BANNED_KEYWORD_PHRASES = BLOCKED_PHRASES
BANNED_REGEX_PATTERNS = [
    r"\bprofit(s|able)?\b",
    r"\bguarantee(d|s)?\b",
    r"\bmake(s|ing)? money\b",
    r"\bwin rate\b",
    r"\bhigh win rate\b",
    r"\bnever lose\b",
    r"\brisk[- ]free\b",
    r"\bzero risk\b",
    r"\bsafe money\b",
    r"\bget rich\b",
    r"\beasy income\b",
    r"\bpassive income\b",
    r"\bcash\b",
    r"\bwealth\b",
    r"\bsure thing\b",
    r"\bcertainty\b",
    r"\binvestment advice\b",
    r"\bpersonalized advice\b",
    r"\bfiduciary\b",
    r"\bstock pick\b",
    r"\bbuy alert\b",
    r"\bsell alert\b",
    r"\btrade signal(s)?\b",
    r"\bcopy trading\b",
    r"\balpaca\b", r"\btd ameritrade\b", r"\brobinhood\b", r"\binteractive brokers\b", r"\be\*trade\b",
    r"\bcharles schwab\b", r"\bfidelity\b", r"\bwebull\b", r"\btradestation\b", r"\bcoinbase\b", r"\bbinance\b", r"\bkraken\b",
    r"\bcrypto\b", r"\bbitcoin\b", r"\bbtc\b", r"\bethereum\b", r"\beth\b", r"\bforex\b", r"\bfx\b",
    r"\boptions\b", r"\bfutures\b", r"\bnft\b", r"\bdefi\b",
    r"\bthis is financial advice\b", r"\bfinancial advice guaranteed\b", r"\bpersonalized financial advice\b",
]

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


def _phrase_matches(text: str, phrase: str) -> bool:
    if not phrase:
        return False

    tokens = [re.escape(part) for part in phrase.strip().split() if part]
    if not tokens:
        return False

    phrase_pattern = r"\s+".join(tokens)
    pattern = rf"(?<![a-z0-9]){phrase_pattern}(?![a-z0-9])"
    return re.search(pattern, text, flags=re.IGNORECASE) is not None


def _find_banned_match(text: str, remove_disclosure: bool = False) -> str | None:
    normalized = text.lower()
    normalized_without_disclosure = normalized.replace(ALLOWED_DISCLOSURE_LOWER, "") if remove_disclosure else normalized

    for phrase in BANNED_KEYWORD_PHRASES:
        if _phrase_matches(normalized_without_disclosure, phrase):
            return phrase

    for pattern in BANNED_REGEX_PATTERNS:
        if re.search(pattern, normalized_without_disclosure, flags=re.IGNORECASE):
            return pattern
    return None


def validate_caption(caption: str) -> tuple[bool, str]:
    if not caption or not caption.strip():
        return False, "empty caption"
    if caption.count(DISCLOSURE) != 1:
        return False, "caption must include disclosure exactly once"

    banned_match = _find_banned_match(caption, remove_disclosure=True)
    if banned_match:
        return False, f"caption contains banned compliance term: {banned_match}"

    if len(caption) < 120 or len(caption) > 1200:
        return False, "caption length out of range"

    if any(p in caption.lower() for p in GENERIC_PHRASES):
        return False, "caption too generic marketing language"

    hashtags = re.findall(r"#\w+", caption)
    if len(hashtags) > 5:
        return False, "too many hashtags"

    emojis = re.findall(r"[\U0001F300-\U0001FAFF]", caption)
    if len(emojis) > 1:
        return False, "too many emojis"

    return True, "ok"


def validate_image_prompt(prompt: str) -> tuple[bool, str]:
    if not prompt or not prompt.strip():
        return False, "image prompt too short"

    banned_match = _find_banned_match(prompt)
    if banned_match:
        return False, f"image prompt contains banned compliance term: {banned_match}"

    if len(prompt.strip()) < 80:
        return False, "image prompt too short"

    lowered = prompt.lower()
    if any(_phrase_matches(lowered, term) for term in ["money", "luxury", "lamborghini", "rolex", "mansion"]):
        return False, "image prompt contains banned cash/luxury symbolism"
    if any(_phrase_matches(lowered, term) for term in ["pnl", "gains", "account balance", "balance screenshot", "fake return"]):
        return False, "image prompt contains banned fake pnl/gains/account balance language"
    if any(_phrase_matches(lowered, term) for term in ["ticker", "buy", "sell", "recommendation", "stock pick"]):
        return False, "image prompt contains banned readable ticker/recommendation language"

    has_scene = any(cue in lowered for cue in SCENE_CUES)
    has_style = any(cue in lowered for cue in STYLE_CUES)
    generic_hits = sum(1 for phrase in GENERIC_IMAGE_ONLY if phrase in lowered)

    if not has_scene:
        return False, "image prompt missing scene/environment cue"
    if not has_style:
        return False, "image prompt missing style/camera/mood cue"
    if generic_hits >= 2 and not (has_scene and has_style):
        return False, "image prompt too generic command center style"

    return True, "ok"
