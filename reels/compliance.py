from __future__ import annotations

BANNED_MARKETING_TERMS = [
    "guaranteed profit",
    "guaranteed profits",
    "guaranteed returns",
    "guaranteed",
    "passive income",
    "make money while you sleep",
    "get rich",
    "risk-free",
    "no risk",
    "signals that win",
    "win rate",
    "100% accurate",
    "easy money",
    "financial advice",
    "buy now",
    "sell now",
]


def validate_compliance_text(text: str, field_name: str) -> None:
    normalized = text.lower()
    for phrase in BANNED_MARKETING_TERMS:
        if phrase in normalized:
            raise ValueError(f"{field_name} contains prohibited marketing/compliance phrase: {phrase}")
