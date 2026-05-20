import re

from prompts import BLOCKED_PHRASES, BRAND_URL, DISCLOSURE, IMAGE_PROMPT_TEMPLATES, needs_risk_disclosure, APPROVED_EMOJIS, MONEY_LUXURY_EMOJIS

GENERIC_PHRASES = ["unlock your potential", "next level", "game changer", "cutting edge", "seamless experience"]
BANNED_REGEX_PATTERNS = [
    r"\bprofit(s|able)?\b", r"\bguarantee(d|s)?\b", r"\bmake(s|ing)? money\b", r"\bwin rate\b",
    r"\brisk[- ]free\b", r"\bget rich\b", r"\beasy income\b", r"\bpassive income\b",
    r"\bbuy (now|this|the)\b", r"\bsell (now|this|the)\b", r"\bnot financial advice\b(?!\. trading involves risk\.)",
]
ALLOWED_URL_PATTERN = re.compile(r"https?://[^\s]+", re.IGNORECASE)
BROKER_REGEX = re.compile(r"\b(alpaca|robinhood|fidelity|webull|etrade|e\*trade|schwab|binance|coinbase|kraken)\b", re.IGNORECASE)

BANNED_IMAGE_TEXT_PATTERNS = ["add bold professional text", "add headline text", "add small footer text", "readable headline", "typography", "labeled sections", "text branding"]

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

    hard_banned_fragments = [
        "visit",
        "learn more at",
        "disclosure:",
        "it does not not financial advice",
    ]
    if any(fragment in lowered for fragment in hard_banned_fragments):
        return False, "caption contains banned malformed fragment"
    if lowered.count("not financial advice") > 1:
        return False, "duplicate Not financial advice"
    if lowered.count("trading involves risk") > 1:
        return False, "duplicate Trading involves risk"
    if caption.count("(") != caption.count(")"):
        return False, "caption has malformed parentheses"

    dangling_cta_fragments = [        "learn more at.",
        "visit at.",
        "visit: .",
        "learn more: .",
        "explore more at.",
        "see more at.",
        "find out more at.",
        "check it out at.",
        "go to.",
    ]
    if any(fragment in lowered for fragment in dangling_cta_fragments):
        return False, "caption contains dangling CTA fragment"


    hashtags = re.findall(r"(?<!\w)#\w+", caption)
    if len(hashtags) != 4:
        return False, "caption must include exactly 4 hashtags"
    if "#XeanVI" not in hashtags:
        return False, "caption must include #XeanVI"

    if "🌈" in caption:
        return False, "caption contains banned emoji"
    emoji_pattern = re.compile("[" + "".join(re.escape(e) for e in APPROVED_EMOJIS + MONEY_LUXURY_EMOJIS + ["🌈"]) + "]")
    found = emoji_pattern.findall(caption)
    approved_count = sum(caption.count(e) for e in APPROVED_EMOJIS)
    if approved_count > 1:
        return False, "caption has more than one emoji"
    if any(e in caption for e in MONEY_LUXURY_EMOJIS):
        return False, "caption contains money/luxury emoji"
    first_line = caption.splitlines()[0] if caption.splitlines() else ""
    if approved_count == 1 and not any(e in first_line for e in APPROVED_EMOJIS):
        return False, "emoji allowed only in hook line"

    if caption.count(BRAND_URL) > 1:
        return False, "duplicate URL"
    words = re.findall(r"\b\w+[\w'-]*\b", caption)
    if len(words) < 35 or len(words) > 140:
        return False, "caption word count out of range"

    needs = needs_risk_disclosure(caption)
    has = bool(DISCLOSURE) and DISCLOSURE.lower() in caption.lower()
    if DISCLOSURE and needs and not has:
        return False, "caption must include disclosure for risk-related content"
    if DISCLOSURE and caption.lower().count(DISCLOSURE.lower()) > 1:
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
    lowered = prompt.lower()
    for pat in BANNED_IMAGE_TEXT_PATTERNS:
        if pat in lowered:
            if pat == "typography" and "no typography" in lowered:
                continue
            return False, f"image prompt requests banned text directive: {pat}"
    if re.search(r"\b(readable text|headline text|footer text|words|letters|labels?)\b", lowered):
        if "no readable text" not in lowered and "no words" not in lowered and "no letters" not in lowered:
            return False, "image prompt requests readable text"
    return True, "ok"
