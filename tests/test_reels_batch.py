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
