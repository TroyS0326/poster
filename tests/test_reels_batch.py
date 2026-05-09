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
    assert summary["total_items"] == 1
    assert summary["success_count"] == 1
    assert summary["failed_count"] == 0
    assert summary["render_failed_count"] == 0


def test_summary_failed_item_includes_topic_and_error(tmp_path: Path) -> None:
    payload = _base_payload()
    payload["items"] = [{"topic": "Topic with bad duration", "slug": "bad_duration", "duration_seconds": "NaN"}]
    summary = run_batch(payload, tmp_path)
    item = summary["items"][0]
    assert item["status"] == "failed"
    assert item["topic"] == "Topic with bad duration"
    assert "must be numeric" in item["error"]


def test_run_report_created_with_slug_and_status(tmp_path: Path) -> None:
    payload = _base_payload()
    payload["items"][0]["slug"] = "report_ok"
    run_batch(payload, tmp_path)
    report_path = tmp_path / "run_report.md"
    assert report_path.exists()
    report_text = report_path.read_text(encoding="utf-8")
    assert "report_ok" in report_text
    assert "success" in report_text


def test_skipped_render_count_only_counts_success_without_render(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> None:
    payload = _base_payload()
    payload["render_mp4"] = False
    payload["items"] = [
        {"topic": "Success without render", "slug": "ok_skip", "render_mp4": False},
        {"topic": "Bad bool value", "slug": "bad_bool", "render_mp4": "false"},
        {"topic": "Render requested fails", "slug": "render_fail", "render_mp4": True},
    ]

    def _raise_render(*args, **kwargs):
        raise RuntimeError("ffmpeg unavailable")

    monkeypatch.setattr("reels.batch.render_reel", _raise_render)
    summary = run_batch(payload, tmp_path)
    report_text = (tmp_path / "run_report.md").read_text(encoding="utf-8")
    assert summary["success_count"] == 1
    assert summary["failed_count"] == 1
    assert summary["render_failed_count"] == 1
    assert "- skipped_render_count: 1" in report_text


def test_summary_item_includes_render_requested(tmp_path: Path) -> None:
    payload = _base_payload()
    payload["items"] = [
        {"topic": "No render", "slug": "no_render", "render_mp4": False},
        {"topic": "With render requested", "slug": "render_req", "render_mp4": True},
    ]
    summary = run_batch(payload, tmp_path)
    assert summary["items"][0]["render_requested"] is False
    assert summary["items"][1]["render_requested"] is True


def test_events_log_created_with_batch_and_item_events(tmp_path: Path) -> None:
    payload = _base_payload()
    payload["items"][0]["slug"] = "event_ok"
    run_batch(payload, tmp_path)
    events_path = tmp_path / "events.jsonl"
    assert events_path.exists()
    lines = [json.loads(line) for line in events_path.read_text(encoding="utf-8").splitlines() if line.strip()]
    names = [line["event"] for line in lines]
    assert "batch_started" in names
    assert "batch_completed" in names
    assert "item_started" in names
    assert "item_completed" in names


def test_events_log_contains_item_failed_for_bad_item(tmp_path: Path) -> None:
    payload = _base_payload()
    payload["items"] = [{"slug": "bad_item"}]
    run_batch(payload, tmp_path)
    events_path = tmp_path / "events.jsonl"
    lines = [json.loads(line) for line in events_path.read_text(encoding="utf-8").splitlines() if line.strip()]
    assert any(line["event"] == "item_failed" for line in lines)


def test_background_written_event_order(tmp_path: Path) -> None:
    payload = _base_payload()
    payload["generate_background"] = True
    payload["items"][0]["slug"] = "event_order"
    run_batch(payload, tmp_path)
    lines = [json.loads(line) for line in (tmp_path / "events.jsonl").read_text(encoding="utf-8").splitlines() if line.strip()]
    item_events = [line["event"] for line in lines if line.get("slug") == "event_order"]
    assert item_events.index("item_started") < item_events.index("background_written") < item_events.index("storyboard_written")


def test_top_level_invalid_boolean_does_not_write_misleading_batch_started(tmp_path: Path) -> None:
    payload = _base_payload()
    payload["generate_background"] = "false"
    with pytest.raises(ValueError, match="generate_background must be a boolean"):
        run_batch(payload, tmp_path)
    events_path = tmp_path / "events.jsonl"
    assert not events_path.exists()
