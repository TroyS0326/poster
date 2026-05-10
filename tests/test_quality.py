from quality import validate_caption, validate_image_prompt
from prompts import DISCLOSURE


def test_quality_requires_disclosure_when_risk_related():
    cap = "Execution discipline matters when market pressure rises and bracket orders are active. Keep a defined process, validate entries and exits, and enforce limits before every live trading decision so emotion does not drive outcomes. XeanVI keeps rules visible and repeatable across sessions so your command center supports judgment, not impulse. "
    ok, reason = validate_caption(cap)
    assert not ok and "disclosure" in reason


def test_quality_allows_non_risk_without_disclosure():
    cap = "Shipping update from the product team: we refined dashboard navigation, reduced clutter in validation panels, and improved audit logs so traders can review workflows faster. This release focuses on usability, architecture clarity, and operator confidence in the command center. Follow for more build notes, and share which module you want to see next in a behind-the-scenes walkthrough."
    ok, _ = validate_caption(cap)
    assert ok


def test_quality_blocks_banned_phrase():
    cap = f"This platform will guarantee outcomes and make money with no effort while every setup wins automatically through signals and certainty for everyone who joins today. Keep following for fast results and easy wins in every market session forever with no drawdown at all. {DISCLOSURE}"
    ok, _ = validate_caption(cap)
    assert not ok


def test_image_prompt_rejects_luxury_money_imagery():
    ok, reason = validate_image_prompt("Cinematic trading room with cash piles, yacht visuals, and fake PnL account balance screenshots, glowing luxury style, dark fintech mood, ultra detailed 16:9 composition")
    assert not ok
    assert "banned" in reason



def test_risk_caption_becomes_valid_after_sanitization():
    from prompts import sanitize_caption_policy

    cap = "Bracket orders and live trading process need discipline, defined checks, and repeatable review loops to avoid emotional decisions."
    sanitized = sanitize_caption_policy(cap, needs_disclosure=True, include_url=False)
    ok, reason = validate_caption(sanitized)
    assert ok, reason
