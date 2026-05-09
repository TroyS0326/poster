import json
from pathlib import Path

import pytest

from reels.config import load_reel_config


def _write(tmp_path: Path, payload: dict, filename: str = "cfg.json") -> Path:
    path = tmp_path / filename
    path.write_text(json.dumps(payload), encoding="utf-8")
    return path


def test_load_reel_config_valid(tmp_path: Path) -> None:
    payload = {
        "title": "Hello",
        "duration_seconds": 6,
        "size": [1080, 1920],
        "scenes": [{"text": "A", "duration": 3}, {"text": "B", "duration": 3}],
    }
    cfg = load_reel_config(_write(tmp_path, payload))
    assert cfg.title == "Hello"
    assert cfg.size == (1080, 1920)
    assert len(cfg.scenes) == 2


def test_load_reel_config_invalid_json(tmp_path: Path) -> None:
    path = tmp_path / "bad.json"
    path.write_text("{", encoding="utf-8")
    with pytest.raises(ValueError):
        load_reel_config(path)


def test_invalid_background_type(tmp_path: Path) -> None:
    payload = {"title": "Hi", "duration_seconds": 5, "background": {"type": "video"}, "scenes": [{"text": "A", "duration": 5}]}
    with pytest.raises(ValueError, match="background.type"):
        load_reel_config(_write(tmp_path, payload))


def test_invalid_hex_color(tmp_path: Path) -> None:
    payload = {"title": "Hi", "duration_seconds": 5, "background": {"type": "solid", "color": "blue"}, "scenes": [{"text": "A", "duration": 5}]}
    with pytest.raises(ValueError, match="hex color"):
        load_reel_config(_write(tmp_path, payload))


def test_image_background_missing_path(tmp_path: Path) -> None:
    payload = {"title": "Hi", "duration_seconds": 5, "background": {"type": "image"}, "scenes": [{"text": "A", "duration": 5}]}
    with pytest.raises(ValueError, match="background.path is required"):
        load_reel_config(_write(tmp_path, payload))


def test_scene_entry_not_dict(tmp_path: Path) -> None:
    payload = {"title": "Hi", "duration_seconds": 5, "scenes": ["not-an-object"]}
    with pytest.raises(ValueError, match=r"scene\[0\] must be an object"):
        load_reel_config(_write(tmp_path, payload))


def test_scene_duration_sum_greater_than_duration_seconds(tmp_path: Path) -> None:
    payload = {"title": "Hi", "duration_seconds": 5, "scenes": [{"text": "A", "duration": 3}, {"text": "B", "duration": 3}]}
    with pytest.raises(ValueError, match="cannot exceed"):
        load_reel_config(_write(tmp_path, payload))


def test_scene_duration_sum_less_than_duration_seconds_allowed(tmp_path: Path) -> None:
    payload = {"title": "Hi", "duration_seconds": 8, "scenes": [{"text": "A", "duration": 2}, {"text": "B", "duration": 2}]}
    cfg = load_reel_config(_write(tmp_path, payload))
    assert cfg.duration_seconds == 8
    assert sum(scene.duration for scene in cfg.scenes) == 4


def test_default_size_and_fps(tmp_path: Path) -> None:
    payload = {"title": "Hi", "duration_seconds": 5, "scenes": [{"text": "A", "duration": 5}]}
    cfg = load_reel_config(_write(tmp_path, payload))
    assert cfg.size == (1080, 1920)
    assert cfg.fps == 24


def test_voiceover_script_field_loads(tmp_path: Path) -> None:
    payload = {
        "title": "Hi",
        "duration_seconds": 5,
        "scenes": [{"text": "A", "duration": 5}],
        "voiceover": {"enabled": True, "provider": "local_audio", "audio_path": "outputs/audio/a.wav", "script": "Scene A."},
    }
    cfg = load_reel_config(_write(tmp_path, payload))
    assert cfg.voiceover.script == "Scene A."
