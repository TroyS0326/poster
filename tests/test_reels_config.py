import json
from pathlib import Path

import pytest

from reels.config import load_reel_config


def test_load_reel_config_valid(tmp_path: Path) -> None:
    payload = {
        "title": "Hello",
        "duration_seconds": 6,
        "size": [1080, 1920],
        "scenes": [{"text": "A", "duration": 3}, {"text": "B", "duration": 3}],
    }
    path = tmp_path / "ok.json"
    path.write_text(json.dumps(payload), encoding="utf-8")

    cfg = load_reel_config(path)
    assert cfg.title == "Hello"
    assert cfg.size == (1080, 1920)
    assert len(cfg.scenes) == 2


def test_load_reel_config_invalid_json(tmp_path: Path) -> None:
    path = tmp_path / "bad.json"
    path.write_text("{", encoding="utf-8")
    with pytest.raises(ValueError):
        load_reel_config(path)


def test_load_reel_config_bad_scene_duration(tmp_path: Path) -> None:
    payload = {
        "title": "Hi",
        "duration_seconds": 5,
        "scenes": [{"text": "A", "duration": 10}],
    }
    path = tmp_path / "bad_duration.json"
    path.write_text(json.dumps(payload), encoding="utf-8")

    with pytest.raises(ValueError):
        load_reel_config(path)
