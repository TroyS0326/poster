import json
from pathlib import Path

import pytest
from moviepy import ColorClip

from reels.config import load_reel_config
from reels.video_assets import load_video_manifest
from reels.video_renderer import render_video_reel


def _make_clip(path: Path, color=(20, 40, 80)):
    ColorClip(size=(360, 640), color=color, duration=2.0).with_fps(24).write_videofile(str(path), codec="libx264", audio=False, logger=None)


def test_video_renderer_creates_mp4(tmp_path: Path):
    clip = tmp_path / "clip.mp4"
    _make_clip(clip)
    manifest = tmp_path / "video_manifest.json"
    manifest.write_text(json.dumps({"clips": [{"id": "one", "path": str(clip), "tags": ["discipline", "rules"], "mood": "focused", "safe_for": ["execution"]}]}), encoding="utf-8")
    cfgf = tmp_path / "reel.json"
    cfgf.write_text(json.dumps({"title": "Execution rules", "duration_seconds": 8, "size": [360, 640], "fps": 24, "background": {"type": "solid", "color": "#111111", "color_end": "#111111"}, "scenes": [{"text": "Follow your execution rules", "duration": 2}, {"text": "Protect risk", "duration": 2}, {"text": "Repeat process", "duration": 2}], "voiceover": {"enabled": False}}), encoding="utf-8")
    out = tmp_path / "out.mp4"
    render_video_reel(load_reel_config(cfgf), out, clips=load_video_manifest(manifest))
    assert out.exists() and out.stat().st_size > 1000


def test_video_renderer_missing_manifest_clear_error(tmp_path: Path):
    with pytest.raises(Exception, match="valid video manifest"):
        load_video_manifest(tmp_path / "none.json")
