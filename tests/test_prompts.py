from prompts import BRAND_URL, DISCLOSURE, IMAGE_PROMPT_TEMPLATES, needs_risk_disclosure, repair_caption_compliance, sanitize_caption_policy, should_include_url


def test_disclosure_needed_for_risk_terms():
    assert needs_risk_disclosure("Bracket orders and risk checks before live trading")


def test_disclosure_not_needed_for_brand_post():
    assert not needs_risk_disclosure("Dashboard architecture update and UI polish")


def test_url_not_in_every_post_deterministic_mix():
    vals = [should_include_url("brand awareness", "founder note", seed=i) for i in range(20)]
    assert any(vals)
    assert not all(vals)


def test_sanitize_adds_once_disclosure_and_url():
    caption = f"Hook line. Insight line. CTA line. {DISCLOSURE} {DISCLOSURE} {BRAND_URL}"
    out = sanitize_caption_policy(caption, needs_disclosure=True, include_url=True)
    assert out.count(DISCLOSURE) == 1
    assert out.count(BRAND_URL) == 1


def test_text_templates_are_explicitly_limited():
    text_enabled = [t for t in IMAGE_PROMPT_TEMPLATES if t["allows_text"]]
    assert len(text_enabled) == 2
    assert all("text" in t["prompt"].lower() for t in text_enabled)


def test_short_caption_expands_to_minimum_words():
    out = sanitize_caption_policy("Discipline first.", needs_disclosure=False, include_url=False)
    assert len(out.split()) >= 45
    assert DISCLOSURE not in out


def test_non_risk_caption_no_forced_disclosure():
    cap = "Product roadmap update with cleaner dashboards and stronger observability for operators."
    out = sanitize_caption_policy(cap, needs_disclosure=False, include_url=False)
    assert DISCLOSURE not in out


def test_url_can_be_appended_and_deduplicated():
    cap = f"Explore the platform {BRAND_URL}"
    out = sanitize_caption_policy(cap, needs_disclosure=False, include_url=True)
    assert out.count(BRAND_URL) == 1


def test_repair_caption_risk_free():
    repaired = repair_caption_compliance("This is a risk-free framework for traders.")
    assert "risk-free" not in repaired.lower()
    assert "structured risk controls" in repaired.lower()


def test_repair_caption_profit():
    repaired = repair_caption_compliance("This process improves profit consistency.")
    assert "profit" not in repaired.lower()


def test_sanitize_removes_dangling_visit_after_url_strip():
    out = sanitize_caption_policy("Learn the workflow. Visit: . https://xeanvi.com", needs_disclosure=False, include_url=False)
    assert "Visit:" not in out


def test_sanitize_removes_partial_disclosure_fragments_before_append():
    caption = "Process discipline matters. Trading involves risk. Not financial advice."
    out = sanitize_caption_policy(caption, needs_disclosure=True, include_url=False)
    assert out.count("Trading involves risk.") == 1
    assert out.count("Not financial advice.") == 1


def test_sanitize_keeps_exactly_one_disclosure_when_required():
    caption = "Review the workflow. Not financial advice. Trading involves risk. Trading involves risk."
    out = sanitize_caption_policy(caption, needs_disclosure=True, include_url=False)
    assert out.count(DISCLOSURE) == 1


def test_repair_softens_unwavering_precision():
    repaired = repair_caption_compliance("Define your rules and execute with unwavering precision.")
    assert "execute with unwavering precision" not in repaired.lower()
    assert "support more consistent rule-following" in repaired


def test_repair_softens_empower_your_trading():
    repaired = repair_caption_compliance("Empower your trading with better tools.")
    assert "empower your trading" not in repaired.lower()
    assert "Build a more disciplined trading process" in repaired


def test_repair_softens_perfect_trade_setup():
    repaired = repair_caption_compliance("Watching a perfect trade setup can trigger hesitation.")
    assert "perfect trade setup" not in repaired.lower()
    assert "qualified setup" in repaired.lower()


def test_repair_replaces_flawless_execution():
    repaired = repair_caption_compliance("This workflow ensures flawless execution in volatile sessions.")
    assert "flawless execution" not in repaired.lower()
    assert "supports more consistent rule-following" in repaired


def test_repair_replaces_freeing_you_from_emotional_pitfalls():
    repaired = repair_caption_compliance("The system focuses on freeing you from emotional pitfalls during entries.")
    assert "freeing you from emotional pitfalls" not in repaired.lower()
    assert "reducing emotional interference" in repaired


def test_repair_replaces_elevate_your_trading_discipline():
    repaired = repair_caption_compliance("Elevate your trading discipline with routine reviews.")
    assert "elevate your trading discipline" not in repaired.lower()
    assert "Build a more disciplined trading process" in repaired
