import json
from pathlib import Path

import pytest

from reels.batch import run_batch
from reels.config import load_reel_config


def _base_payload() -> dict:
    return {
        "brand": "xeanvi",
        "template": "mistake",
        "visual_style": "market_grid",
        "duration_seconds": 18,
        "scene_count": 4,
        "generate_background": False,
        "generate_voiceover_placeholder": False,
        "render_mp4": False,
        "items": [{"topic": "The cost of breaking your own trading rules", "slug": "one"}],
    }


def test_valid_batch_generates_json_and_summary(tmp_path: Path) -> None:
    payload = _base_payload()
    payload["items"] = [
        {"topic": "The cost of breaking your own trading rules", "slug": "breaking_rules"},
        {"topic": "Why paper testing protects your process", "slug": "paper_testing"},
    ]
    summary = run_batch(payload, tmp_path)
    assert (tmp_path / "summary.json").exists()
    assert (tmp_path / "breaking_rules" / "breaking_rules.json").exists()
    assert (tmp_path / "paper_testing" / "paper_testing.json").exists()
    assert len(summary["items"]) == 2


def test_background_png_generated_when_enabled(tmp_path: Path) -> None:
    payload = _base_payload()
    payload["generate_background"] = True
    payload["items"][0]["slug"] = "bg"
    run_batch(payload, tmp_path)
    assert (tmp_path / "bg" / "bg.png").exists()


def test_silent_wav_generated_when_enabled(tmp_path: Path) -> None:
    payload = _base_payload()
    payload["generate_voiceover_placeholder"] = True
    payload["items"][0]["slug"] = "wav"
    run_batch(payload, tmp_path)
    assert (tmp_path / "wav" / "wav.wav").exists()


def test_duplicate_slug_rejected(tmp_path: Path) -> None:
    payload = _base_payload()
    payload["items"] = [{"topic": "Topic A", "slug": "dup"}, {"topic": "Topic B", "slug": "dup"}]
    summary = run_batch(payload, tmp_path)
    assert any(item["status"] == "failed" and "duplicate slug" in item.get("error", "") for item in summary["items"])


def test_missing_topic_rejected(tmp_path: Path) -> None:
    payload = _base_payload()
    payload["items"] = [{"slug": "missing_topic"}]
    summary = run_batch(payload, tmp_path)
    assert summary["items"][0]["status"] == "failed"


def test_item_level_overrides_work(tmp_path: Path) -> None:
    payload = _base_payload()
    payload["items"] = [{"topic": "Why rules matter", "slug": "ovr", "scene_count": 3, "duration_seconds": 12, "template": "checklist"}]
    run_batch(payload, tmp_path)
    cfg = load_reel_config(tmp_path / "ovr" / "ovr.json")
    assert len(cfg.scenes) == 3
    assert cfg.duration_seconds == 12


def test_compliance_banned_topic_fails_only_that_item(tmp_path: Path) -> None:
    payload = _base_payload()
    payload["items"] = [
        {"topic": "guaranteed profits from trading", "slug": "bad"},
        {"topic": "Why paper testing protects your process", "slug": "good"},
    ]
    summary = run_batch(payload, tmp_path)
    statuses = {item["slug"]: item["status"] for item in summary["items"]}
    assert statuses["bad"] == "failed"
    assert statuses["good"] == "success"


def test_render_false_does_not_attempt_render(tmp_path: Path) -> None:
    payload = _base_payload()
    payload["render_mp4"] = False
    payload["items"][0]["slug"] = "no_render"
    summary = run_batch(payload, tmp_path)
    assert summary["items"][0].get("mp4_path") is None
    assert not (tmp_path / "no_render" / "no_render.mp4").exists()


def test_generated_json_loads_through_loader(tmp_path: Path) -> None:
    payload = _base_payload()
    payload["items"][0]["slug"] = "loader"
    run_batch(payload, tmp_path)
    cfg = load_reel_config(tmp_path / "loader" / "loader.json")
    assert cfg.title


def test_empty_items_rejected(tmp_path: Path) -> None:
    payload = _base_payload()
    payload["items"] = []
    with pytest.raises(ValueError, match="non-empty"):
        run_batch(payload, tmp_path)


@pytest.mark.parametrize(
    ("field", "message"),
    [
        ("generate_background", "generate_background must be a boolean"),
        ("generate_voiceover_placeholder", "generate_voiceover_placeholder must be a boolean"),
        ("render_mp4", "render_mp4 must be a boolean"),
    ],
)
def test_top_level_string_boolean_rejected(tmp_path: Path, field: str, message: str) -> None:
    payload = _base_payload()
    payload[field] = "false"
    with pytest.raises(ValueError, match=message):
        run_batch(payload, tmp_path)


def test_item_level_string_boolean_override_rejected(tmp_path: Path) -> None:
    payload = _base_payload()
    payload["items"] = [{"topic": "Why rules matter", "slug": "bad_bool", "render_mp4": "false"}]
    summary = run_batch(payload, tmp_path)
    assert summary["items"][0]["status"] == "failed"
    assert "items[0].render_mp4 must be a boolean" in summary["items"][0]["error"]


def test_xeanvi_default_visual_style_is_consistent_for_background_and_storyboard(tmp_path: Path) -> None:
    payload = _base_payload()
    payload.pop("visual_style")
    payload["generate_background"] = True
    payload["items"][0]["slug"] = "style_default"
    run_batch(payload, tmp_path)
    storyboard = json.loads((tmp_path / "style_default" / "style_default.json").read_text(encoding="utf-8"))
    assert storyboard["visual"]["style"] == "fintech_dark"
    assert (tmp_path / "style_default" / "style_default.png").exists()


def test_item_visual_style_override_is_used_consistently(tmp_path: Path) -> None:
    payload = _base_payload()
    payload["generate_background"] = True
    payload["items"] = [{"topic": "Why rules matter", "slug": "style_override", "visual_style": "workstation"}]
    run_batch(payload, tmp_path)
    storyboard = json.loads((tmp_path / "style_override" / "style_override.json").read_text(encoding="utf-8"))
    assert storyboard["visual"]["style"] == "workstation"
    assert (tmp_path / "style_override" / "style_override.png").exists()


def test_summary_success_includes_topic_and_slug(tmp_path: Path) -> None:
    payload = _base_payload()
    payload["items"][0]["slug"] = "summary_ok"
    summary = run_batch(payload, tmp_path)
    item = summary["items"][0]
    assert item["status"] == "success"
    assert item["slug"] == "summary_ok"
    assert item["topic"] == payload["items"][0]["topic"]


def test_summary_failed_item_includes_topic_and_error(tmp_path: Path) -> None:
    payload = _base_payload()
    payload["items"] = [{"topic": "Topic with bad duration", "slug": "bad_duration", "duration_seconds": "NaN"}]
    summary = run_batch(payload, tmp_path)
    item = summary["items"][0]
    assert item["status"] == "failed"
    assert item["topic"] == "Topic with bad duration"
    assert "must be numeric" in item["error"]
