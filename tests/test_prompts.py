from prompts import DISCLOSURE, BRAND_URL, IMAGE_PROMPT_TEMPLATES, needs_risk_disclosure, sanitize_caption_policy, should_include_url


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
