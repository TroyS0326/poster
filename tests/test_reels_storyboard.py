import json
from pathlib import Path

import pytest

from reels.config import load_reel_config
from reels.storyboard import _allocate_scene_durations, _validate_inputs, generate_storyboard


def test_duration_allocation_count_matches_scene_count() -> None:
    durations = _allocate_scene_durations(18, 4)
    assert len(durations) == 4


def test_duration_allocation_sum_never_exceeds_total() -> None:
    durations = _allocate_scene_durations(20, 3)
    assert sum(durations) <= 20


def test_20_seconds_3_scenes_loadable_by_config_loader(tmp_path: Path) -> None:
    payload = generate_storyboard(topic="Why traders need rules", duration_seconds=20, scene_count=3)
    path = tmp_path / "storyboard_20_3.json"
    path.write_text(json.dumps(payload), encoding="utf-8")
    cfg = load_reel_config(path)
    assert len(cfg.scenes) == 3
    assert sum(scene.duration for scene in cfg.scenes) <= cfg.duration_seconds


def test_10_seconds_3_scenes_loadable_by_config_loader(tmp_path: Path) -> None:
    payload = generate_storyboard(topic="Why traders need rules", duration_seconds=10, scene_count=3)
    path = tmp_path / "storyboard_10_3.json"
    path.write_text(json.dumps(payload), encoding="utf-8")
    cfg = load_reel_config(path)
    assert len(cfg.scenes) == 3
    assert sum(scene.duration for scene in cfg.scenes) <= cfg.duration_seconds


def test_default_storyboard_still_works() -> None:
    payload = generate_storyboard(topic="Why traders need rules, not motivation")
    assert payload["duration_seconds"] == 18
    assert len(payload["scenes"]) == 4


def test_generated_scene_durations_are_all_positive() -> None:
    payload = generate_storyboard(topic="Rule-based execution beats emotional trading")
    assert all(scene["duration"] > 0 for scene in payload["scenes"])


def test_generated_json_can_be_loaded_by_config_loader(tmp_path: Path) -> None:
    payload = generate_storyboard(topic="Rule-based execution beats emotional trading")
    path = tmp_path / "storyboard.json"
    path.write_text(json.dumps(payload), encoding="utf-8")
    cfg = load_reel_config(path)
    assert cfg.title
    assert len(cfg.scenes) == 4


def test_local_storyboard_generation_creates_valid_json() -> None:
    payload = generate_storyboard(topic="Why traders need rules, not motivation")
    assert payload["title"]
    assert isinstance(payload["scenes"], list)
    assert len(payload["scenes"]) == 4
    assert payload["background"]["type"] in {"solid", "gradient"}
    assert payload["duration_seconds"] == 18
    assert payload["fps"] == 24
    assert payload["size"] == [1080, 1920]


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
