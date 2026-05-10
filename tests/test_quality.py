from quality import validate_caption, validate_image_prompt
from prompts import DISCLOSURE


def _base_caption():
    return "Hook line.\n\nInsight one for disciplined process.\nInsight two with review steps.\n\nXeanVI helps enforce user-defined rules and keeps validation visible.\n\nBuild the process before the pressure hits.\n\n#XeanVI #TradingDiscipline #RiskControls #RuleBasedExecution"


def test_validate_caption_rejects_3_hashtags():
    cap = _base_caption().replace("#RuleBasedExecution", "")
    ok, reason = validate_caption(cap)
    assert not ok and "exactly 4 hashtags" in reason


def test_validate_caption_rejects_5_hashtags():
    cap = _base_caption() + " #TradingRules"
    ok, reason = validate_caption(cap)
    assert not ok and "exactly 4 hashtags" in reason


def test_validate_caption_rejects_rainbow_emoji():
    cap = _base_caption().replace("Hook line.", "Hook line 🌈.")
    ok, reason = validate_caption(cap)
    assert not ok and "banned emoji" in reason


def test_validate_caption_rejects_more_than_one_emoji():
    cap = _base_caption().replace("Hook line.", "Hook line 🧠 ✅.")
    ok, reason = validate_caption(cap)
    assert not ok and "more than one emoji" in reason


def test_validate_image_prompt_rejects_readable_text_requests():
    ok, reason = validate_image_prompt("Create dashboard and add headline text with typography and labeled sections")
    assert not ok


def test_validate_image_prompt_allows_no_readable_text_safety_language():
    ok, reason = validate_image_prompt("Create premium fintech dashboard with abstract UI panels, no readable text, no words, no letters, no typography, no logos")
    assert ok, reason
