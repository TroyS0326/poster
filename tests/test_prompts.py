import re

from prompts import APPROVED_EMOJIS, BRAND_URL, CONTENT_PILLARS, DISCLOSURE, IMAGE_PROMPT_TEMPLATES, POST_ARCHETYPES, build_caption, build_hashtags, needs_risk_disclosure, repair_caption_compliance, sanitize_caption_policy, should_include_url
from quality import validate_caption

WORD_RE = re.compile(r"\b[\w'-]+\b")


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


def test_image_prompt_templates_all_disallow_text():
    assert all(not t["allows_text"] for t in IMAGE_PROMPT_TEMPLATES)


def test_image_prompt_templates_remove_text_directives():
    blob = "\n".join(t["prompt"] for t in IMAGE_PROMPT_TEMPLATES)
    assert "Add bold professional text" not in blob
    assert "Add headline text" not in blob
    assert "Add small footer text" not in blob


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


def test_sanitize_removes_learn_more_at_fragment():
    out = sanitize_caption_policy("Refine process discipline. Learn more at.", needs_disclosure=False, include_url=False)
    assert "learn more at." not in out.lower()


def test_sanitize_removes_visit_at_fragment():
    out = sanitize_caption_policy("Review your checklist. Visit at.", needs_disclosure=False, include_url=False)
    assert "visit at." not in out.lower()


def test_sanitize_removes_explore_more_at_fragment():
    out = sanitize_caption_policy("Improve review quality. Explore more at.", needs_disclosure=False, include_url=False)
    assert "explore more at." not in out.lower()


def test_repair_replaces_elevate_your_practice():
    repaired = repair_caption_compliance("Elevate your practice with repeatable drills.")
    assert "elevate your practice" not in repaired.lower()
    assert "Build a more structured practice routine" in repaired


def test_repair_replaces_winning_virtual_trades():
    repaired = repair_caption_compliance("The objective is winning virtual trades before going live.")
    assert "winning virtual trades" not in repaired.lower()
    assert "passing simulated trades" in repaired.lower()


def test_sanitize_allows_clean_disclosure_and_url_ending():
    out = sanitize_caption_policy(
        "Elevate your practice. Learn more at.",
        needs_disclosure=True,
        include_url=True,
    )
    assert out.endswith(f"{DISCLOSURE} {BRAND_URL}")
    assert "learn more at." not in out.lower()


def test_build_caption_returns_line_breaks_and_4_hashtags():
    cap = build_caption("Risk controls before entries", "checklist", include_url=False, needs_disclosure=True)
    assert "\n\n" in cap
    assert len([w for w in cap.split() if w.startswith("#")]) == 4


def test_build_caption_disclosure_exactly_once_when_required():
    cap = build_caption("Risk controls before entries", "checklist", include_url=False, needs_disclosure=True)
    assert cap.count(DISCLOSURE) == 1


def test_build_caption_without_disclosure_when_not_required():
    cap = build_caption("Founder/build-in-public", "founder note", include_url=False, needs_disclosure=False)
    if needs_risk_disclosure(cap):
        assert DISCLOSURE in cap
    else:
        assert DISCLOSURE not in cap


def test_build_caption_url_exactly_once_when_requested():
    cap = build_caption("Trust/transparency", "founder note", include_url=True, needs_disclosure=False)
    assert cap.count(BRAND_URL) == 1


def test_build_caption_never_has_forbidden_cta_fragments():
    cap = build_caption("Risk controls", "checklist", include_url=True, needs_disclosure=True)
    lowered = cap.lower()
    assert "visit" not in lowered
    assert "learn more at" not in lowered
    assert "disclosure:" not in lowered


def test_build_caption_always_has_xeanvi_hashtag():
    cap = build_caption("Risk controls", "checklist", include_url=False, needs_disclosure=False)
    assert "#XeanVI" in cap


def test_build_caption_uses_at_most_one_approved_emoji_and_never_rainbow():
    cap = build_caption("Risk controls", "checklist", include_url=False, needs_disclosure=False)
    assert "🌈" not in cap
    count = sum(cap.count(e) for e in APPROVED_EMOJIS)
    assert count <= 1


def test_build_hashtags_exactly_four():
    tags = build_hashtags("paper trading", "checklist")
    assert len(tags) == 4 and tags[0] == "#XeanVI"


def test_build_caption_changes_with_different_seeds():
    a = build_caption("Risk controls before entries", "checklist", include_url=False, needs_disclosure=True, seed=1)
    b = build_caption("Risk controls before entries", "checklist", include_url=False, needs_disclosure=True, seed=2)
    assert a != b


def test_build_hashtags_rotates_with_seed():
    tags_a = tuple(build_hashtags("Risk controls before entries", "checklist", seed=11))
    tags_b = tuple(build_hashtags("Risk controls before entries", "checklist", seed=12))
    assert len(tags_a) == 4
    assert tags_a[0] == "#XeanVI"
    assert len(set(tags_a)) == 4
    assert tags_a != tags_b


def test_seeded_caption_sample_has_multiple_unique_and_hashtag_sets():
    captions = [
        build_caption("Risk controls before entries", "checklist", include_url=(i % 2 == 0), needs_disclosure=True, seed=i)
        for i in range(10)
    ]
    assert len(set(captions)) >= 4
    hashtag_sets = set()
    for cap in captions:
        tags = tuple(w for w in cap.split() if w.startswith("#"))
        assert len(tags) == 4
        hashtag_sets.add(tags)
    assert len(hashtag_sets) >= 3


def test_build_caption_no_money_or_rainbow_emoji():
    banned = {"🌈", "💰", "💸", "🤑", "💎", "🏎️", "🚘", "🛥️", "🛩️", "🏰", "👑"}
    cap = build_caption("Risk controls", "checklist", include_url=False, needs_disclosure=False, seed=99)
    assert not any(e in cap for e in banned)


def test_build_caption_matrix_always_validates_final_caption():
    for idx, pillar in enumerate(CONTENT_PILLARS):
        for archetype in POST_ARCHETYPES:
            for seed in range(10):
                include_url = ((idx + seed) % 2 == 0)
                needs = needs_risk_disclosure(f"{pillar} {archetype} raw")
                caption = build_caption(pillar, archetype, include_url, needs, seed=seed)
                ok, reason = validate_caption(caption)
                assert ok, reason


def test_build_caption_matrix_word_count_45_to_90():
    for idx, pillar in enumerate(CONTENT_PILLARS):
        for archetype in POST_ARCHETYPES:
            for seed in range(20):
                include_url = ((idx + seed) % 2 == 0)
                needs = needs_risk_disclosure(f"{pillar} {archetype} raw")
                caption = build_caption(pillar, archetype, include_url, needs, seed=seed)
                word_count = len(WORD_RE.findall(caption))
                assert 45 <= word_count <= 90, (pillar, archetype, seed, word_count, caption)


def test_risk_term_disclosure_regression():
    phrases = [
        "no rule, no trade",
        "the setup failed",
        "entry criteria",
        "post-loss reset",
        "position sizing",
        "volatility spiked",
        "live capital",
        "invalidation first",
        "bracket boundary",
        "stop placement",
    ]
    for phrase in phrases:
        text = f"Hook. Insight. {phrase}. #XeanVI #TradingRules #RiskControls #ExecutionDiscipline"
        assert needs_risk_disclosure(text), phrase


def test_final_caption_disclosure_regression_matrix():
    for pillar in CONTENT_PILLARS:
        for archetype in POST_ARCHETYPES:
            for seed in range(21):
                include_url = (seed % 2 == 0)
                caption = build_caption(pillar, archetype, include_url, needs_disclosure=False, seed=seed)
                if needs_risk_disclosure(caption):
                    assert DISCLOSURE in caption
                assert caption.count(DISCLOSURE) <= 1


def test_caption_format_regression():
    samples = [
        build_caption(CONTENT_PILLARS[i % len(CONTENT_PILLARS)], POST_ARCHETYPES[i % len(POST_ARCHETYPES)], include_url=(i % 2 == 0), needs_disclosure=False, seed=i)
        for i in range(24)
    ]
    for cap in samples:
        blocks = [b.strip() for b in cap.split("\n\n") if b.strip()]
        assert len(blocks) in (5, 6), cap
        assert len(blocks[0].splitlines()) == 1
        assert len(blocks[1].splitlines()) == 2
        assert blocks[2].startswith("XeanVI")
        assert not blocks[3].startswith("#")
        if len(blocks) == 6:
            assert blocks[4] == DISCLOSURE
            hashtag_block = blocks[5]
        else:
            hashtag_block = blocks[4]
        tags = hashtag_block.split()
        assert len(tags) == 4
        assert all(t.startswith("#") for t in tags)
        assert "#XeanVI" in tags


def test_seeded_caption_uniqueness_50_samples():
    captions = [
        build_caption("Risk controls before entries", "checklist", include_url=(i % 2 == 0), needs_disclosure=True, seed=i)
        for i in range(50)
    ]
    assert len(set(captions)) >= 25
    hook_lines = {c.splitlines()[0] for c in captions}
    assert len(hook_lines) >= 10
    normalized_hooks = {
        " ".join(w for w in line.split() if w not in APPROVED_EMOJIS).strip()
        for line in hook_lines
    }
    assert len(normalized_hooks) >= 5
    hashtag_sets = {
        tuple(line.split())
        for c in captions
        for line in c.splitlines()
        if line.startswith("#")
    }
    assert len(hashtag_sets) >= 10


def test_pillar_specific_language_presence():
    keyword_map = {
        "Revenge trading after one bad loss": ["loss", "revenge", "reset", "next decision"],
        "Paper trading as a serious testing lab, not a toy": ["paper", "simulated", "lab", "testing"],
        "Bracket orders as emotional guardrails": ["bracket", "guardrail", "boundary"],
        "The difference between scanning and chasing": ["scanner", "scanning", "chasing", "filter"],
        "Overtrading from boredom": ["bored", "boredom", "low-quality"],
        "Building a playbook before live capital": ["playbook", "rules", "criteria"],
    }
    for pillar, words in keyword_map.items():
        caps = [build_caption(pillar, "lesson learned", include_url=False, needs_disclosure=True, seed=s) for s in range(8)]
        joined = "\n".join(caps).lower()
        assert any(w in joined for w in words), f"missing keyword for {pillar}"


def test_compliance_regression_100_samples():
    banned_phrases = [
        "profit", "profits", "profitable", "guaranteed", "guarantee", "passive income", "win rate", "risk-free",
        "get rich", "make money", "easy income", "flawless execution", "perfect setup", "best strategy",
        "smarter execution", "empower your trading", "elevate your trading",
    ]
    banned_emoji = {"🌈", "💰", "💸", "🤑", "💎", "🏎️", "🚘", "🛥️", "🛩️", "🏰", "👑"}
    samples = []
    for i in range(100):
        pillar = CONTENT_PILLARS[i % len(CONTENT_PILLARS)]
        archetype = POST_ARCHETYPES[i % len(POST_ARCHETYPES)]
        cap = build_caption(pillar, archetype, include_url=(i % 3 == 0), needs_disclosure=True, seed=i)
        samples.append(cap)
    for cap in samples:
        assert not any(e in cap for e in banned_emoji)
        assert sum(cap.count(e) for e in APPROVED_EMOJIS) <= 1
        tags = [w for w in cap.split() if w.startswith("#")]
        assert len(tags) == 4
        assert "#XeanVI" in tags
        lowered = cap.lower()
        assert not any(bp in lowered for bp in banned_phrases)


def test_build_caption_url_behavior_exact():
    with_url = build_caption("Trust/transparency", "founder note", include_url=True, needs_disclosure=False, seed=7)
    without_url = build_caption("Trust/transparency", "founder note", include_url=False, needs_disclosure=False, seed=7)
    assert with_url.count(BRAND_URL) == 1
    assert BRAND_URL not in without_url
