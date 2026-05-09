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
    monkeypatch.setattr(autopost, "render_video_reel", lambda cfg, out, clips: calls.__setitem__("video", calls["video"] + 1) or Path(out).write_bytes(b"x"))
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
