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
    "desk", "workstation", "notebook", "keyboard", "coffee", "monitor", "chair",
    "flat lay", "abstract", "interface", "dashboard cards", "rule-board", "process diagram",
    "product ui", "mockup", "monitor glow", "empty desk",
]
STYLE_CUES = [
    "cinematic", "editorial", "realistic", "isometric", "lighting", "mood", "depth of field",
    "palette", "glow", "contrast", "minimal", "fintech", "vertical", "1080x1350",
]
GENERIC_IMAGE_ONLY = [
    "command center", "dashboard", "dark-mode", "dark mode", "ui panels", "fintech ui",
]
ANATOMY_RISK_TERMS = [
    "hand", "hands", "finger", "fingers", "face", "person", "people", "human", "humans", "man", "woman", "body", "arm",
    "holding", "over-the-shoulder", "portrait", "beard", "eyes",
]
BLOCKED_ANATOMY_PHRASES = ["paper held", "holding paper", "handwritten chart held", "person holding"]

SAFE_NEGATED_ANATOMY_PHRASES = [
    "no hands", "no hand", "no fingers", "no finger", "no faces", "no face", "no arms", "no arm",
    "no body parts", "no people", "no person", "no humans", "no human", "without hands", "without faces",
    "without people", "silhouette-free", "object-only",
]


def _remove_safe_negated_anatomy_phrases(text: str) -> str:
    cleaned = text.lower()
    for phrase in SAFE_NEGATED_ANATOMY_PHRASES:
        pattern = rf"(?<![a-z0-9]){re.escape(phrase)}(?![a-z0-9])"
        cleaned = re.sub(pattern, " ", cleaned, flags=re.IGNORECASE)
    return re.sub(r"\s+", " ", cleaned).strip()


SAFE_VISUAL_CUES = [
    "product ui", "mockup", "empty desk", "flat lay", "abstract", "interface", "dashboard cards",
    "workstation", "notebook", "keyboard", "monitor glow", "rule-board", "process diagram",
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

    words = re.findall(r"\b\w+[\w'-]*\b", caption)
    if len(words) < 44 or len(words) > 85:
        return False, "caption word count out of range"

    if any(p in caption.lower() for p in GENERIC_PHRASES):
        return False, "caption too generic marketing language"

    hashtags = re.findall(r"#\w+", caption)
    if len(hashtags) > 4:
        return False, "too many hashtags"

    if "\n" not in caption:
        return False, "caption must include line breaks"

    for line in caption.splitlines():
        stripped = line.strip()
        if not stripped or stripped.startswith("#"):
            continue
        if len(stripped) > 220:
            return False, "caption has overly long paragraph line"

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

    if any(_phrase_matches(lowered, phrase) for phrase in BLOCKED_ANATOMY_PHRASES):
        return False, "image prompt contains blocked anatomy phrase"

    if "silhouette" in lowered and not ("no visible hands" in lowered and "no visible face" in lowered and "no visible limbs" in lowered):
        return False, "silhouette usage must explicitly ban visible hands/face/limbs"

    anatomy_scan_text = _remove_safe_negated_anatomy_phrases(lowered)

    if any(_phrase_matches(anatomy_scan_text, term) for term in ANATOMY_RISK_TERMS):
        return False, "image prompt contains anatomy-risk terms"
    if any(_phrase_matches(lowered, term) for term in ["money", "luxury", "lamborghini", "rolex", "mansion"]):
        return False, "image prompt contains banned cash/luxury symbolism"
    if any(_phrase_matches(lowered, term) for term in ["pnl", "gains", "account balance", "balance screenshot", "fake return"]):
        return False, "image prompt contains banned fake pnl/gains/account balance language"
    if any(_phrase_matches(lowered, term) for term in ["ticker", "buy", "sell", "recommendation", "stock pick"]):
        return False, "image prompt contains banned readable ticker/recommendation language"

    has_scene = any(cue in lowered for cue in SCENE_CUES)
    has_safe_visual = any(cue in lowered for cue in SAFE_VISUAL_CUES)
    has_style = any(cue in lowered for cue in STYLE_CUES)
    generic_hits = sum(1 for phrase in GENERIC_IMAGE_ONLY if phrase in lowered)

    if not has_scene:
        return False, "image prompt missing scene/environment cue"
    if not has_safe_visual:
        return False, "image prompt missing safe visual type cue"
    if not has_style:
        return False, "image prompt missing style/camera/mood cue"
    if generic_hits >= 2 and not (has_scene and has_style):
        return False, "image prompt too generic command center style"

    return True, "ok"
