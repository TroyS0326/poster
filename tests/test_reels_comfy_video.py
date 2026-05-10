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


def _post_resp(payload):
    class Resp:
        def __init__(self, p): self._p = p
        def raise_for_status(self): return None
        def json(self): return self._p
    return Resp(payload)


def test_prompt_node_text_negative_seed(monkeypatch, tmp_path):
    wf = tmp_path / "wf.json"
    wf.write_text(json.dumps({"1": {"inputs": {"text": ""}}, "2": {"inputs": {"text": ""}}, "3": {"inputs": {"seed": 0}}}), encoding="utf-8")
    monkeypatch.setattr("reels.video_provider_comfy.random.randint", lambda *a, **k: 42)
    monkeypatch.setattr("reels.video_provider_comfy.requests.post", lambda *a, **k: _post_resp({"prompt_id": "abc"}))

    class Hist:
        def raise_for_status(self): return None
        def json(self): return {"abc": {"outputs": {"n": {"videos": [{"filename": "a.mp4", "subfolder": "", "type": "output"}]}}}}

    class View:
        content = b"bin"
        def raise_for_status(self): return None

    sent = {}
    def fake_get(url, **kwargs):
        if "history" in url:
            return Hist()
        sent.update(kwargs["params"])
        return View()

    monkeypatch.setattr("reels.video_provider_comfy.requests.get", fake_get)
    out = tmp_path / "out.mp4"
    generate_comfy_video_clip("hello", out, api_url="http://x", workflow_path=wf, prompt_node_id="1", negative_prompt_node_id="2", seed_node_id="3", width=1, height=1, frames=1, fps=1, timeout_seconds=2, poll_seconds=0)
    payload = json.loads(wf.read_text())
    assert out.exists()
    assert sent["filename"] == "a.mp4"


def test_prompt_node_value_negative_value_seed_noise_seed(monkeypatch, tmp_path):
    wf = tmp_path / "wf.json"
    workflow_data = {"1": {"inputs": {"value": ""}}, "2": {"inputs": {"value": ""}}, "3": {"inputs": {"noise_seed": 0}}}
    wf.write_text(json.dumps(workflow_data), encoding="utf-8")
    monkeypatch.setattr("reels.video_provider_comfy.random.randint", lambda *a, **k: 77)

    captured_prompt = {}
    def fake_post(url, json=None, **kwargs):
        captured_prompt.update(json["prompt"])
        return _post_resp({"prompt_id": "abc"})

    class Hist:
        def raise_for_status(self): return None
        def json(self): return {"abc": {"outputs": {"n": {"gifs": [{"filename": "a.gif", "subfolder": "", "type": "output"}]}}}}

    class View:
        content = b"gif-bytes"
        def raise_for_status(self): return None

    monkeypatch.setattr("reels.video_provider_comfy.requests.post", fake_post)
    monkeypatch.setattr("reels.video_provider_comfy.requests.get", lambda url, **k: Hist() if "history" in url else View())
    out = tmp_path / "out.gif"
    generate_comfy_video_clip("hello2", out, api_url="http://x", workflow_path=wf, prompt_node_id="1", negative_prompt_node_id="2", seed_node_id="3", width=1, height=1, frames=1, fps=1, timeout_seconds=2, poll_seconds=0)
    assert out.read_bytes() == b"gif-bytes"
    assert captured_prompt["1"]["inputs"]["value"] == "hello2"
    assert captured_prompt["2"]["inputs"]["value"].startswith("no readable text")
    assert captured_prompt["3"]["inputs"]["noise_seed"] == 77


def test_generation_poll_success_videos(monkeypatch, tmp_path):
    wf = tmp_path / "wf.json"; wf.write_text(json.dumps({"1": {"inputs": {}}}), encoding="utf-8")
    out = tmp_path / "out.mp4"
    monkeypatch.setattr("reels.video_provider_comfy.requests.post", lambda *a, **k: _post_resp({"prompt_id": "abc"}))
    monkeypatch.setattr("reels.video_provider_comfy.requests.get", lambda url, **k: _post_resp({"abc": {"outputs": {"n": {"videos": [{"filename": "a.mp4", "subfolder": "", "type": "output"}]}}}}) if "history" in url else type("V", (), {"content": b"bin", "raise_for_status": lambda self: None})())
    p = generate_comfy_video_clip("p", out, api_url="http://x", workflow_path=wf, prompt_node_id="1", negative_prompt_node_id=None, seed_node_id=None, width=1, height=1, frames=1, fps=1, timeout_seconds=2, poll_seconds=0)
    assert p.exists()


def test_no_downloadable_output_error(monkeypatch, tmp_path):
    wf = tmp_path / "wf.json"; wf.write_text(json.dumps({"1": {"inputs": {}}}), encoding="utf-8")
    monkeypatch.setattr("reels.video_provider_comfy.requests.post", lambda *a, **k: _post_resp({"prompt_id": "abc"}))
    monkeypatch.setattr("reels.video_provider_comfy.requests.get", lambda *a, **k: _post_resp({"abc": {"outputs": {"n": {"audio": [{"filename": "a.wav"}]}}}}))
    with pytest.raises(ComfyUIVideoError, match="output keys"):
        generate_comfy_video_clip("p", tmp_path / "o.mp4", api_url="http://x", workflow_path=wf, prompt_node_id="1", negative_prompt_node_id=None, seed_node_id=None, width=1, height=1, frames=1, fps=1, timeout_seconds=2, poll_seconds=0)


def test_timeout_no_video(monkeypatch, tmp_path):
    wf = tmp_path / "wf.json"; wf.write_text(json.dumps({"1": {"inputs": {}}}), encoding="utf-8")
    class Hist:
        def raise_for_status(self): return None
        def json(self): return {"abc": {"outputs": {}}}
    monkeypatch.setattr("reels.video_provider_comfy.requests.post", lambda *a, **k: _post_resp({"prompt_id": "abc"}))
    monkeypatch.setattr("reels.video_provider_comfy.requests.get", lambda *a, **k: Hist())
    with pytest.raises(ComfyUIVideoError, match="Timed out"):
        generate_comfy_video_clip("p", tmp_path / "o.mp4", api_url="http://x", workflow_path=wf, prompt_node_id="1", negative_prompt_node_id=None, seed_node_id=None, width=1, height=1, frames=1, fps=1, timeout_seconds=0, poll_seconds=0)


def test_ensure_scene_video_clips_reuse_existing(tmp_path):
    d = tmp_path / "item"; d.mkdir(); (d / "video_scene_01.mp4").write_bytes(b"x")
    cfg = type("C", (), {"max_generated_clips_per_reel": 3, "provider": "comfy", "generate_video_clips": True})()
    got = ensure_scene_video_clips({"title": "t", "scenes": [{"text": "a"}]}, d, cfg)
    assert got == [str(d / "video_scene_01.mp4")]
