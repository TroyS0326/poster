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


@pytest.mark.parametrize("template", ["discipline", "mistake", "checklist", "myth", "before-after"])
def test_each_template_produces_loadable_config(tmp_path: Path, template: str) -> None:
    payload = generate_storyboard(topic="Why rules matter", template=template)
    path = tmp_path / f"{template}.json"
    path.write_text(json.dumps(payload), encoding="utf-8")
    cfg = load_reel_config(path)
    assert len(cfg.scenes) == 4


@pytest.mark.parametrize("brand", ["generic", "xeanvi"])
def test_each_brand_produces_loadable_config(tmp_path: Path, brand: str) -> None:
    payload = generate_storyboard(topic="Risk controls first", brand=brand)
    path = tmp_path / f"{brand}.json"
    path.write_text(json.dumps(payload), encoding="utf-8")
    cfg = load_reel_config(path)
    assert cfg.title


def test_unsupported_template_rejected() -> None:
    with pytest.raises(ValueError, match="unsupported template"):
        generate_storyboard(topic="Topic", template="unknown")


def test_unsupported_brand_rejected() -> None:
    with pytest.raises(ValueError, match="unsupported brand"):
        generate_storyboard(topic="Topic", brand="unknown")


def test_xeanvi_brand_uses_safe_language() -> None:
    payload = generate_storyboard(topic="Why rules matter", brand="xeanvi", template="mistake")
    combined = " ".join(scene["text"] for scene in payload["scenes"]).lower()
    assert "rule-based" in combined
    assert "playbook" in combined or "validation" in combined
    banned = ["guaranteed", "passive income", "make money while you sleep", "signals that win"]
    assert not any(term in combined for term in banned)


@pytest.mark.parametrize("scene_count", [2, 3, 4, 6])
def test_generated_scene_count_matches_request(scene_count: int) -> None:
    payload = generate_storyboard(topic="Topic", template="checklist", scene_count=scene_count)
    assert len(payload["scenes"]) == scene_count
    assert all(scene["text"].strip() for scene in payload["scenes"])
