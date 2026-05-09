import json
from pathlib import Path

import pytest

from reels.video_assets import VideoManifestError, load_video_manifest, select_clip


def test_manifest_loading(tmp_path: Path):
    clip = tmp_path / "c.mp4"
    clip.write_bytes(b"x")
    mf = tmp_path / "video_manifest.json"
    mf.write_text(json.dumps({"clips": [{"id": "c1", "path": str(clip), "tags": ["discipline"], "mood": "focused", "safe_for": ["rules"]}]}), encoding="utf-8")
    clips = load_video_manifest(mf)
    assert clips[0].id == "c1"


def test_manifest_missing_rejected(tmp_path: Path):
    with pytest.raises(VideoManifestError):
        load_video_manifest(tmp_path / "missing.json")


def test_clip_selection_by_topic_tags(tmp_path: Path):
    clips = [
        type("C", (), {"id": "stress", "tags": ("mistake", "stress", "red"), "safe_for": (), "mood": "tense"})(),
        type("C", (), {"id": "calm", "tags": ("practice", "calm", "journal"), "safe_for": (), "mood": "calm"})(),
        type("C", (), {"id": "discipline", "tags": ("discipline", "system", "focus"), "safe_for": ("rules",), "mood": "focused"})(),
    ]
    assert select_clip(clips, topic="revenge trading", scene_text="", template="", tone="stress").id == "stress"
    assert select_clip(clips, topic="paper testing", scene_text="", template="", tone="discipline").id == "calm"
    assert select_clip(clips, topic="execution rules", scene_text="", template="", tone="discipline").id == "discipline"
