import json
from pathlib import Path

import pytest

from reels.config import load_reel_config
from reels.storyboard import _validate_inputs, generate_storyboard


def test_local_storyboard_generation_creates_valid_json() -> None:
    payload = generate_storyboard(topic="Why traders need rules, not motivation")
    assert payload["title"]
    assert isinstance(payload["scenes"], list)
    assert len(payload["scenes"]) == 4
    assert payload["background"]["type"] in {"solid", "gradient"}
    assert payload["duration_seconds"] == 18
    assert payload["fps"] == 24
    assert payload["size"] == [1080, 1920]


def test_generated_json_can_be_loaded_by_config_loader(tmp_path: Path) -> None:
    payload = generate_storyboard(topic="Rule-based execution beats emotional trading")
    path = tmp_path / "storyboard.json"
    path.write_text(json.dumps(payload), encoding="utf-8")
    cfg = load_reel_config(path)
    assert cfg.title
    assert len(cfg.scenes) == 4


def test_empty_topic_rejected(tmp_path: Path) -> None:
    with pytest.raises(ValueError, match="topic must not be empty"):
        _validate_inputs("", 18, 4, "gradient", tmp_path / "out.json")


def test_invalid_scene_count_rejected(tmp_path: Path) -> None:
    with pytest.raises(ValueError, match="scene_count"):
        _validate_inputs("topic", 18, 1, "gradient", tmp_path / "out.json")


def test_invalid_duration_rejected(tmp_path: Path) -> None:
    with pytest.raises(ValueError, match="too short"):
        _validate_inputs("topic", 5, 4, "gradient", tmp_path / "out.json")


def test_unsupported_background_type_rejected(tmp_path: Path) -> None:
    with pytest.raises(ValueError, match="background_type"):
        _validate_inputs("topic", 18, 4, "image", tmp_path / "out.json")


def test_output_structure_fields_present() -> None:
    payload = generate_storyboard(topic="Paper testing builds confidence")
    expected_fields = {"title", "scenes", "background", "duration_seconds", "fps", "size"}
    assert expected_fields.issubset(payload.keys())
