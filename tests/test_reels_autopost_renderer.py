import json
from pathlib import Path

from reels import autopost


def _prep(tmp_path: Path):
    run_dir = tmp_path / "outputs/queue/day_03/a"
    run_dir.mkdir(parents=True)
    (run_dir / "a.json").write_text("{}", encoding="utf-8")
    (run_dir.parent / "summary.json").write_text(json.dumps({"items": [{"slug": "a", "json_path": str(run_dir / 'a.json')}]}), encoding="utf-8")
    q = tmp_path / "queue.json"
    q.write_text(json.dumps({"output_root": "outputs/queue", "runs": [{"run_id": "day_03", "items": [{"topic": "A", "slug": "a"}]}], "batch_defaults": {}}), encoding="utf-8")
    return q


def _set_cfg(monkeypatch):
    cfg = type("Cfg", (), {"cleanup_after_success": False, "delete_after_success_extensions": (), "post_dry_run": True, "post_to_instagram": True, "post_to_facebook": True})()
    monkeypatch.setattr(autopost, "load_publish_config", lambda: cfg)


def test_autopost_uses_video_renderer(monkeypatch, tmp_path: Path):
    monkeypatch.chdir(tmp_path)
    q = _prep(tmp_path)
    _set_cfg(monkeypatch)
    calls = {"video": 0}
    monkeypatch.setenv("REELS_RENDERER", "video")
    monkeypatch.setattr(autopost, "load_reel_config", lambda p: object())
    monkeypatch.setattr(autopost, "load_video_manifest", lambda p: [object()])
    monkeypatch.setattr(autopost, "render_video_reel", lambda cfg, out, clips, generated_scene_clips=None: calls.__setitem__("video", calls["video"] + 1) or Path(out).write_bytes(b"x"))
    monkeypatch.setattr(autopost, "publish_reel", lambda **k: {"instagram": {"status": "planned"}, "facebook": {"status": "planned"}, "video_url": "u"})
    autopost.run_autopost(q, "day_03", "https://example", dry_run=True)
    assert calls["video"] == 1


def test_autopost_uses_legacy_renderer(monkeypatch, tmp_path: Path):
    monkeypatch.chdir(tmp_path)
    q = _prep(tmp_path)
    _set_cfg(monkeypatch)
    calls = {"legacy": 0}
    monkeypatch.setenv("REELS_RENDERER", "legacy")
    monkeypatch.setattr(autopost, "load_reel_config", lambda p: object())
    monkeypatch.setattr(autopost, "render_reel", lambda cfg, out: calls.__setitem__("legacy", calls["legacy"] + 1) or Path(out).write_bytes(b"x"))
    monkeypatch.setattr(autopost, "publish_reel", lambda **k: {"instagram": {"status": "planned"}, "facebook": {"status": "planned"}, "video_url": "u"})
    autopost.run_autopost(q, "day_03", "https://example", dry_run=True)
    assert calls["legacy"] == 1

def test_autopost_video_comfy_calls_clip_generation(monkeypatch, tmp_path: Path):
    monkeypatch.chdir(tmp_path)
    q = _prep(tmp_path)
    _set_cfg(monkeypatch)
    monkeypatch.setenv("REELS_RENDERER", "video")
    monkeypatch.setenv("REELS_VIDEO_PROVIDER", "comfy")
    monkeypatch.setenv("COMFYUI_PROMPT_NODE_ID", "1")
    monkeypatch.setenv("COMFYUI_PROMPT_NODE_ID", "1")
    calls = {"clips": 0}
    monkeypatch.setattr(autopost, "load_reel_config", lambda p: type("Cfg", (), {"title": "t", "scenes": [type("S", (), {"text": "x"})()]})())
    monkeypatch.setattr(autopost, "ensure_scene_video_clips", lambda storyboard, item_dir, config=None: calls.__setitem__("clips", calls["clips"] + 1) or [str(item_dir / "video_scene_01.mp4")])
    monkeypatch.setattr(autopost, "load_video_manifest", lambda p: [object()])
    monkeypatch.setattr(autopost, "render_video_reel", lambda cfg, out, clips, generated_scene_clips=None: Path(out).write_bytes(b"x"))
    monkeypatch.setattr(autopost, "publish_reel", lambda **k: {"instagram": {"status": "planned"}, "facebook": {"status": "planned"}, "video_url": "u"})
    autopost.run_autopost(q, "day_03", "https://example", dry_run=True)
    assert calls["clips"] == 1


def test_autopost_video_comfy_clip_failure_marks_render_failed(monkeypatch, tmp_path: Path):
    monkeypatch.chdir(tmp_path)
    q = _prep(tmp_path)
    _set_cfg(monkeypatch)
    monkeypatch.setenv("REELS_RENDERER", "video")
    monkeypatch.setenv("REELS_VIDEO_PROVIDER", "comfy")
    monkeypatch.setattr(autopost, "load_reel_config", lambda p: type("Cfg", (), {"title": "t", "scenes": [type("S", (), {"text": "x"})()]})())
    monkeypatch.setattr(autopost, "ensure_scene_video_clips", lambda *a, **k: (_ for _ in ()).throw(RuntimeError("clip boom")))
    monkeypatch.setattr(autopost, "publish_reel", lambda **k: (_ for _ in ()).throw(RuntimeError("should not call")))
    result = autopost.run_autopost(q, "day_03", "https://example", dry_run=True)
    assert result["items"][0]["status"] == "render_failed"


def test_autopost_video_comfy_generated_clips_skip_manifest(monkeypatch, tmp_path: Path):
    monkeypatch.chdir(tmp_path)
    q = _prep(tmp_path)
    _set_cfg(monkeypatch)
    monkeypatch.setenv("REELS_RENDERER", "video")
    monkeypatch.setenv("REELS_VIDEO_PROVIDER", "comfy")
    monkeypatch.setenv("COMFYUI_PROMPT_NODE_ID", "1")

    called = {"manifest": 0, "render": 0}

    monkeypatch.setattr(autopost, "load_reel_config", lambda p: type("Cfg", (), {"title": "t", "scenes": [type("S", (), {"text": "x"})()]})())
    monkeypatch.setattr(autopost, "ensure_scene_video_clips", lambda storyboard, item_dir, config=None: [str(item_dir / "video_scene_01.mp4")])

    def _manifest(_):
        called["manifest"] += 1
        raise AssertionError("load_video_manifest should not be called when generated clips exist")

    def _render(cfg, out, clips, generated_scene_clips=None):
        called["render"] += 1
        assert clips == []
        assert generated_scene_clips and generated_scene_clips[0].endswith("video_scene_01.mp4")
        Path(out).write_bytes(b"x")

    monkeypatch.setattr(autopost, "load_video_manifest", _manifest)
    monkeypatch.setattr(autopost, "render_video_reel", _render)
    monkeypatch.setattr(autopost, "publish_reel", lambda **k: {"instagram": {"status": "planned"}, "facebook": {"status": "planned"}, "video_url": "u"})

    autopost.run_autopost(q, "day_03", "https://example", dry_run=True)
    assert called["manifest"] == 0
    assert called["render"] == 1


def test_autopost_video_manifest_provider_loads_manifest(monkeypatch, tmp_path: Path):
    monkeypatch.chdir(tmp_path)
    q = _prep(tmp_path)
    _set_cfg(monkeypatch)
    monkeypatch.setenv("REELS_RENDERER", "video")
    monkeypatch.setenv("REELS_VIDEO_PROVIDER", "manifest")

    called = {"manifest": 0}
    monkeypatch.setattr(autopost, "load_reel_config", lambda p: object())

    def _manifest(path):
        called["manifest"] += 1
        return [object()]

    monkeypatch.setattr(autopost, "load_video_manifest", _manifest)
    monkeypatch.setattr(autopost, "render_video_reel", lambda cfg, out, clips, generated_scene_clips=None: Path(out).write_bytes(b"x"))
    monkeypatch.setattr(autopost, "publish_reel", lambda **k: {"instagram": {"status": "planned"}, "facebook": {"status": "planned"}, "video_url": "u"})

    autopost.run_autopost(q, "day_03", "https://example", dry_run=True)
    assert called["manifest"] == 1
