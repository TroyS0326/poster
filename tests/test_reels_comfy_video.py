import json
from pathlib import Path

import pytest

from reels.video_clip_generation import ensure_scene_video_clips
from reels.video_prompts import build_scene_video_prompt
from reels.video_provider_comfy import ComfyUIVideoError, check_comfyui_health, generate_comfy_video_clip


def test_prompt_builder_includes_safety_and_tone():
    p = build_scene_video_prompt("revenge trading", "avoid impulsive entries")
    assert "vertical 9:16" in p.lower()
    assert "no logos" in p.lower()
    assert "financial advice" in p.lower()
    assert "impulsive" in p.lower()


def test_comfy_health_success_failure(monkeypatch):
    class R:
        ok = True
    monkeypatch.setattr("reels.video_provider_comfy.requests.get", lambda *a, **k: R())
    assert check_comfyui_health("http://x") is True
    monkeypatch.setattr("reels.video_provider_comfy.requests.get", lambda *a, **k: (_ for _ in ()).throw(Exception("x")))
    assert check_comfyui_health("http://x") is False


def test_missing_workflow_raises(tmp_path):
    with pytest.raises(ComfyUIVideoError, match="workflow missing"):
        generate_comfy_video_clip("p", tmp_path / "o.mp4", api_url="http://x", workflow_path=tmp_path / "none.json", prompt_node_id="1", negative_prompt_node_id=None, seed_node_id=None, width=1, height=1, frames=1, fps=1, timeout_seconds=1, poll_seconds=1)


def test_missing_prompt_node_raises(tmp_path):
    wf = tmp_path / "wf.json"
    wf.write_text(json.dumps({"2": {"inputs": {}}}), encoding="utf-8")
    with pytest.raises(ComfyUIVideoError, match="PROMPT_NODE_ID"):
        generate_comfy_video_clip("p", tmp_path / "o.mp4", api_url="http://x", workflow_path=wf, prompt_node_id="1", negative_prompt_node_id=None, seed_node_id=None, width=1, height=1, frames=1, fps=1, timeout_seconds=1, poll_seconds=1)


def test_generation_poll_success(monkeypatch, tmp_path):
    wf = tmp_path / "wf.json"; wf.write_text(json.dumps({"1": {"inputs": {}}}), encoding="utf-8")
    out = tmp_path / "out.mp4"
    class Resp:
        def __init__(self, payload=None, content=b"v"):
            self._p = payload or {}
            self.content = content
        def raise_for_status(self):
            return None
        def json(self):
            return self._p
    monkeypatch.setattr("reels.video_provider_comfy.requests.post", lambda *a, **k: Resp({"prompt_id": "abc"}))
    monkeypatch.setattr("reels.video_provider_comfy.requests.get", lambda url, **k: Resp({"abc": {"outputs": {"n": {"videos": [{"filename": "a.mp4", "subfolder": "", "type": "output"}]}}}}) if "history" in url else Resp({}, b"bin"))
    p = generate_comfy_video_clip("p", out, api_url="http://x", workflow_path=wf, prompt_node_id="1", negative_prompt_node_id=None, seed_node_id=None, width=1, height=1, frames=1, fps=1, timeout_seconds=2, poll_seconds=0)
    assert p.exists()


def test_timeout_no_video(monkeypatch, tmp_path):
    wf = tmp_path / "wf.json"; wf.write_text(json.dumps({"1": {"inputs": {}}}), encoding="utf-8")
    class Resp:
        def raise_for_status(self): return None
        def json(self): return {"prompt_id": "abc"}
    class Hist:
        def raise_for_status(self): return None
        def json(self): return {"abc": {"outputs": {}}}
    monkeypatch.setattr("reels.video_provider_comfy.requests.post", lambda *a, **k: Resp())
    monkeypatch.setattr("reels.video_provider_comfy.requests.get", lambda *a, **k: Hist())
    with pytest.raises(ComfyUIVideoError, match="Timed out"):
        generate_comfy_video_clip("p", tmp_path / "o.mp4", api_url="http://x", workflow_path=wf, prompt_node_id="1", negative_prompt_node_id=None, seed_node_id=None, width=1, height=1, frames=1, fps=1, timeout_seconds=0, poll_seconds=0)


def test_ensure_scene_video_clips_reuse_existing(tmp_path):
    d = tmp_path / "item"; d.mkdir(); (d / "video_scene_01.mp4").write_bytes(b"x")
    cfg = type("C", (), {"max_generated_clips_per_reel": 3, "provider": "comfy", "generate_video_clips": True})()
    got = ensure_scene_video_clips({"title": "t", "scenes": [{"text": "a"}]}, d, cfg)
    assert got == [str(d / "video_scene_01.mp4")]
