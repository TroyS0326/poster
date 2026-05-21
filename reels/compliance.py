"""
FB/IG compliance layer — keeps us from getting banned.

Meta's 2026 enforcement priorities:
  1. No financial advice (buy/sell/hold recommendations)
  2. No guaranteed profit claims
  3. No misleading performance representations
  4. No impersonation of licensed advisors
  5. No content that demotes reach (watermarks, cross-platform reposts)

What we CAN do:
  - Educational content about trading psychology/discipline
  - Sharing personal experience (clearly as experience, not advice)
  - Promoting a trading tool/platform (XEANVI)
  - Discussing risk management concepts
"""
from __future__ import annotations
import re, logging

logger = logging.getLogger(__name__)

# ── Hard blocks — these WILL get flagged/banned ──────────────────────────────
BANNED_PHRASES = [
    r"\bbuy\s+(now|this|it|in|signal)\b",
    r"\bsell\s+(now|this|signal|alert)\b",
    r"\bguaranteed?\s+(profit|return|gain|income|money)\b",
    r"\b\d+\s*%\s+(return|profit|gain|monthly|weekly|daily|guaranteed)\b",
    r"\b(risk[- ]free|no[- ]risk)\b",
    r"\b(financial|investment)\s+advi[sc]e\b",
    r"\b(licensed|certified|registered)\s+(trader|advisor|broker)\b",
    r"\bsec\s+(approved|registered|compliant)\b",
    r"\b(double|triple|10x|100x)\s+your\s+(money|account|investment)\b",
    r"\bpast\s+performance\s+(guarantee|ensure|predict)\b",
]

# ── Soft warnings — review before posting ───────────────────────────────────
WARN_PHRASES = [
    r"\bprofit\b",
    r"\breturns?\b",
    r"\binvest(ment|ing)?\b",
    r"\bsignals?\b",
    r"\bcopy\s+trad(e|ing)\b",
    r"\bmanaged\s+account\b",
]

# Required disclaimer for caption when financial terms are used
CAPTION_DISCLAIMER = (
    "⚠️ Not financial advice. Trading involves substantial risk of loss. "
    "For educational purposes only."
)

SCRIPT_DISCLAIMER = ""  # Don't speak disclaimers — kills the energy. Caption only.


def validate_compliance_text(text: str, context: str = "script") -> None:
    """
    Raise ValueError if text contains banned phrases.
    Log warnings for soft phrases.
    """
    text_lower = text.lower()

    for pattern in BANNED_PHRASES:
        if re.search(pattern, text_lower):
            match = re.search(pattern, text_lower)
            raise ValueError(
                f"[COMPLIANCE] Banned phrase in {context}: "
                f"'{match.group()}' — remove or rewrite before posting"
            )

    warn_hits = []
    for pattern in WARN_PHRASES:
        if re.search(pattern, text_lower):
            m = re.search(pattern, text_lower)
            warn_hits.append(m.group())

    if warn_hits:
        logger.warning(
            "[COMPLIANCE] Soft flag in %s — review: %s",
            context, ", ".join(set(warn_hits))
        )


def build_compliant_caption(raw_caption: str, add_disclaimer: bool = True) -> str:
    """
    Clean a caption and add disclaimer if needed.
    Never modifies the tone — just appends what's needed.
    """
    caption = raw_caption.strip()

    # Check if it needs disclaimer
    needs_disclaimer = any(
        re.search(p, caption.lower()) for p in WARN_PHRASES
    )

    if needs_disclaimer and add_disclaimer:
        caption = f"{caption}\n\n{CAPTION_DISCLAIMER}"

    # Enforce caption length (FB/IG optimal: under 2200 chars, ideal under 400)
    if len(caption) > 2200:
        caption = caption[:2197] + "..."

    return caption


def is_safe_to_post(script: str, caption: str) -> tuple[bool, list[str]]:
    """
    Full compliance check before posting.
    Returns (safe: bool, issues: list[str])
    """
    issues = []

    for pattern in BANNED_PHRASES:
        for text in [script, caption]:
            if re.search(pattern, text.lower()):
                m = re.search(pattern, text.lower())
                issues.append(f"Banned: '{m.group()}'")

    return len(issues) == 0, issues
