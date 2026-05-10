import re

from prompts import BLOCKED_PHRASES, BRAND_URL, DISCLOSURE, IMAGE_PROMPT_TEMPLATES, needs_risk_disclosure

GENERIC_PHRASES = ["unlock your potential", "next level", "game changer", "cutting edge", "seamless experience"]
BANNED_REGEX_PATTERNS = [
    r"\bprofit(s|able)?\b", r"\bguarantee(d|s)?\b", r"\bmake(s|ing)? money\b", r"\bwin rate\b",
    r"\brisk[- ]free\b", r"\bget rich\b", r"\beasy income\b", r"\bpassive income\b",
    r"\bbuy (now|this|the)\b", r"\bsell (now|this|the)\b", r"\bnot financial advice\b(?!\. trading involves risk\.)",
]
ALLOWED_URL_PATTERN = re.compile(r"https?://[^\s]+", re.IGNORECASE)
BROKER_REGEX = re.compile(r"\b(alpaca|robinhood|fidelity|webull|etrade|e\*trade|schwab|binance|coinbase|kraken)\b", re.IGNORECASE)

OVERCLAIM_PHRASES = [
    "flawless execution",
    "guaranteed execution",
    "removes emotion",
    "removes emotional barriers",
    "free from emotional pitfalls",
    "emotion-proof",
    "smarter execution",
    "elevate your trading",
    "empower your trading",
    "perfect trade setup",
    "best strategies",
]


def _find_banned_match(text: str) -> str | None:
    lower = text.lower()
    for phrase in BLOCKED_PHRASES:
        if phrase in lower:
            return phrase
    for pattern in BANNED_REGEX_PATTERNS:
        if re.search(pattern, lower, flags=re.IGNORECASE):
            return pattern
    return None


def validate_caption(caption: str) -> tuple[bool, str]:
    if not caption or not caption.strip():
        return False, "empty caption"
    words = re.findall(r"\b\w+[\w'-]*\b", caption)
    if len(words) < 45 or len(words) > 90:
        return False, "caption word count out of range"
    banned_match = _find_banned_match(caption)
    if banned_match:
        return False, f"caption contains banned compliance term: {banned_match}"
    if BROKER_REGEX.search(caption):
        return False, "caption contains broker name"
    if any(p in caption.lower() for p in GENERIC_PHRASES):
        return False, "caption too generic marketing language"
    lowered = caption.lower()
    for phrase in OVERCLAIM_PHRASES:
        if phrase in lowered:
            return False, f"caption contains overclaim or hype phrase: {phrase}"

    needs = needs_risk_disclosure(caption)
    has = DISCLOSURE.lower() in caption.lower()
    if needs and not has:
        return False, "caption must include disclosure for risk-related content"
    if caption.lower().count(DISCLOSURE.lower()) > 1:
        return False, "duplicate disclosure"

    urls = ALLOWED_URL_PATTERN.findall(caption)
    if any(url.rstrip('.,)') != BRAND_URL for url in urls):
        return False, "caption contains non-approved URL"
    return True, "ok"


def validate_image_prompt(prompt: str) -> tuple[bool, str]:
    if not prompt or len(prompt.strip()) < 80:
        return False, "image prompt too short"
    safe_negative_phrases = [
        "no profit guarantees",
        "no guaranteed returns",
        "no profit promises",
        "no profit claims",
        "no profit screenshots",
        "no fake profit screenshots",
        "no exaggerated profits",
        "no unrealistic claims",
        "no guaranteed outcomes",
        "no guaranteed results",
    ]
    sanitized_for_scan = prompt.lower()
    for safe_phrase in safe_negative_phrases:
        sanitized_for_scan = sanitized_for_scan.replace(safe_phrase, "")

    banned_match = _find_banned_match(sanitized_for_scan)
    if banned_match:
        return False, f"image prompt contains banned compliance term: {banned_match}"
    lowered = prompt.lower()
    for disallowed in ["$", "dollar", "cash", "yacht", "mansion", "rolex", "broker logo", "fake pnl", "account balance"]:
        if disallowed in lowered:
            return False, "image prompt contains banned cash/luxury or fake performance language"
    allows_text = any(t["allows_text"] and t["prompt"].lower() in lowered for t in IMAGE_PROMPT_TEMPLATES)
    if "add bold professional text" in lowered or "add headline text" in lowered:
        if not allows_text:
            return False, "image prompt text is only allowed in text-enabled templates"
    return True, "ok"
