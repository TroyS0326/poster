import json
from pathlib import Path

import pytest

from reels import autopost


def _make_queue(tmp_path: Path):
    q = tmp_path / "queue.json"
    q.write_text(json.dumps({
        "output_root": "outputs/queue",
        "runs": [{"run_id": "day_03", "items": [
            {"topic": "A", "slug": "a"}, {"topic": "B", "slug": "b"}, {"topic": "C", "slug": "c"}, {"topic": "D", "slug": "d"}
        ]}],
        "batch_defaults": {"brand": "xeanvi", "template": "mistake", "duration_seconds": 18, "scene_count": 4, "render_mp4": False, "generate_background": False, "generate_voiceover_placeholder": False}
    }), encoding="utf-8")
    return q


def _set_cfg(monkeypatch, *, post_dry_run=True, post_to_instagram=True, post_to_facebook=True):
    cfg = type("Cfg", (), {
        "cleanup_after_success": True,
        "delete_after_success_extensions": (".mp4", ".wav", ".mp3", ".png"),
        "post_dry_run": post_dry_run,
        "post_to_instagram": post_to_instagram,
        "post_to_facebook": post_to_facebook,
    })()
    monkeypatch.setattr(autopost, "load_publish_config", lambda: cfg)


def test_autopost_renders_missing_mp4_before_publish(tmp_path, monkeypatch):
    monkeypatch.chdir(tmp_path)
    run_dir = tmp_path / "outputs/queue/day_03/a"
    run_dir.mkdir(parents=True)
    (run_dir / "a.json").write_text("{}", encoding="utf-8")
    (run_dir.parent / "summary.json").write_text(json.dumps({"items": [{"slug": "a", "json_path": str(run_dir / 'a.json')}]}), encoding="utf-8")
    _set_cfg(monkeypatch, post_dry_run=False)

    monkeypatch.setattr(autopost, "load_reel_config", lambda p: object())
    monkeypatch.setattr(autopost, "render_reel", lambda cfg, out: Path(out).write_bytes(b"mp4"))
    monkeypatch.setattr(autopost, "publish_reel", lambda **k: {"instagram": {"status": "success"}, "facebook": {"status": "success"}})

    result = autopost.run_autopost(_make_queue(tmp_path), "day_03", "https://example.trycloudflare.com", dry_run=False)
    assert result["items"][0]["mp4_path"].endswith("a.mp4")
    events = (run_dir.parent / "publish_events.jsonl").read_text(encoding="utf-8")
    assert "render_written" in events


def test_autopost_render_failure_skips_publish(tmp_path, monkeypatch):
    monkeypatch.chdir(tmp_path)
    run_dir = tmp_path / "outputs/queue/day_03/a"
    run_dir.mkdir(parents=True)
    (run_dir / "a.json").write_text("{}", encoding="utf-8")
    (run_dir.parent / "summary.json").write_text(json.dumps({"items": [{"slug": "a", "json_path": str(run_dir / 'a.json')}]}), encoding="utf-8")
    _set_cfg(monkeypatch, post_dry_run=False)

    monkeypatch.setattr(autopost, "load_reel_config", lambda p: object())
    monkeypatch.setattr(autopost, "render_reel", lambda cfg, out: (_ for _ in ()).throw(RuntimeError("boom")))
    called = {"n": 0}
    monkeypatch.setattr(autopost, "publish_reel", lambda **k: called.__setitem__("n", called["n"] + 1))

    result = autopost.run_autopost(_make_queue(tmp_path), "day_03", "https://example.trycloudflare.com", dry_run=False)
    assert result["items"][0]["status"] == "render_failed"
    assert called["n"] == 0
    assert "render_failed" in (run_dir.parent / "publish_events.jsonl").read_text(encoding="utf-8")


def test_autopost_dry_run_renders_and_deletes_nothing(tmp_path, monkeypatch):
    monkeypatch.chdir(tmp_path)
    run_dir = tmp_path / "outputs/queue/day_03/a"
    run_dir.mkdir(parents=True)
    (run_dir / "a.json").write_text("{}", encoding="utf-8")
    (run_dir / "a.wav").write_bytes(b"wav")
    (run_dir.parent / "summary.json").write_text(json.dumps({"items": [{"slug": "a", "json_path": str(run_dir / 'a.json')}]}), encoding="utf-8")
    _set_cfg(monkeypatch, post_dry_run=True)

    monkeypatch.setattr(autopost, "load_reel_config", lambda p: object())
    monkeypatch.setattr(autopost, "render_reel", lambda cfg, out: Path(out).write_bytes(b"mp4"))
    monkeypatch.setattr(autopost, "publish_reel", lambda **k: {"instagram": {"status": "planned"}, "facebook": {"status": "planned"}, "video_url": "u"})

    autopost.run_autopost(_make_queue(tmp_path), "day_03", "https://example.trycloudflare.com", dry_run=True)
    assert (run_dir / "a.mp4").exists()
    assert (run_dir / "a.wav").exists()


def test_autopost_success_cleanup_selected_platform_only(tmp_path, monkeypatch):
    monkeypatch.chdir(tmp_path)
    run_dir = tmp_path / "outputs/queue/day_03/a"
    run_dir.mkdir(parents=True)
    (run_dir / "a.json").write_text("{}", encoding="utf-8")
    (run_dir / "a.mp4").write_bytes(b"mp4")
    (run_dir / "a.wav").write_bytes(b"wav")
    (run_dir / "a.png").write_bytes(b"png")
    (run_dir.parent / "summary.json").write_text(json.dumps({"items": [{"slug": "a", "json_path": str(run_dir / 'a.json'), "mp4_path": str(run_dir / 'a.mp4')}]}), encoding="utf-8")
    _set_cfg(monkeypatch, post_dry_run=False, post_to_instagram=True, post_to_facebook=False)

    monkeypatch.setattr(autopost, "publish_reel", lambda **k: {"instagram": {"status": "success"}, "facebook": None})

    result = autopost.run_autopost(_make_queue(tmp_path), "day_03", "https://example.trycloudflare.com", dry_run=False)
    assert result["platform"] == "instagram"
    assert not (run_dir / "a.mp4").exists()
    assert not (run_dir / "a.wav").exists()
    assert not (run_dir / "a.png").exists()
    assert (run_dir / "a.json").exists()


def test_autopost_failed_publish_keeps_files(tmp_path, monkeypatch):
    monkeypatch.chdir(tmp_path)
    run_dir = tmp_path / "outputs/queue/day_03/a"
    run_dir.mkdir(parents=True)
    (run_dir / "a.json").write_text("{}", encoding="utf-8")
    (run_dir / "a.mp4").write_bytes(b"mp4")
    (run_dir.parent / "summary.json").write_text(json.dumps({"items": [{"slug": "a", "json_path": str(run_dir / 'a.json'), "mp4_path": str(run_dir / 'a.mp4')}]}), encoding="utf-8")
    _set_cfg(monkeypatch, post_dry_run=False, post_to_instagram=True, post_to_facebook=True)
    monkeypatch.setattr(autopost, "publish_reel", lambda **k: {"instagram": {"status": "success"}, "facebook": {"status": "failed"}})

    autopost.run_autopost(_make_queue(tmp_path), "day_03", "https://example.trycloudflare.com", dry_run=False)
    assert (run_dir / "a.mp4").exists()


def test_autopost_platform_config_none_requires_dry_run(tmp_path, monkeypatch):
    monkeypatch.chdir(tmp_path)
    run_dir = tmp_path / "outputs/queue/day_03/a"
    run_dir.mkdir(parents=True)
    (run_dir / "a.json").write_text("{}", encoding="utf-8")
    (run_dir / "a.mp4").write_bytes(b"mp4")
    (run_dir.parent / "summary.json").write_text(json.dumps({"items": [{"slug": "a", "json_path": str(run_dir / 'a.json'), "mp4_path": str(run_dir / 'a.mp4')}]}), encoding="utf-8")
    _set_cfg(monkeypatch, post_dry_run=False, post_to_instagram=False, post_to_facebook=False)

    with pytest.raises(ValueError):
        autopost.run_autopost(_make_queue(tmp_path), "day_03", "https://example.trycloudflare.com", dry_run=False)


def test_autopost_cfg_dry_run_forces_publish_dry_run(tmp_path, monkeypatch):
    monkeypatch.chdir(tmp_path)
    run_dir = tmp_path / "outputs/queue/day_03/a"
    run_dir.mkdir(parents=True)
    (run_dir / "a.json").write_text("{}", encoding="utf-8")
    (run_dir / "a.mp4").write_bytes(b"mp4")
    (run_dir.parent / "summary.json").write_text(json.dumps({"items": [{"slug": "a", "json_path": str(run_dir / 'a.json'), "mp4_path": str(run_dir / 'a.mp4')}]}), encoding="utf-8")
    _set_cfg(monkeypatch, post_dry_run=True, post_to_instagram=True, post_to_facebook=True)

    captured = {}
    def _pub(**kwargs):
        captured["dry_run"] = kwargs["dry_run"]
        return {"instagram": {"status": "planned"}, "facebook": {"status": "planned"}, "video_url": "u"}
    monkeypatch.setattr(autopost, "publish_reel", _pub)

    result = autopost.run_autopost(_make_queue(tmp_path), "day_03", "https://example.trycloudflare.com", dry_run=False)
    assert result["dry_run"] is True
    assert captured["dry_run"] is True
    assert (run_dir / "a.mp4").exists()


def test_autopost_stale_summary_missing_json_triggers_regeneration(tmp_path, monkeypatch):
    monkeypatch.chdir(tmp_path)
    run_dir = tmp_path / "outputs/queue/day_03"
    run_dir.mkdir(parents=True)
    stale_json = run_dir / "a/a.json"
    (run_dir / "summary.json").write_text(json.dumps({"items": [{"slug": "a", "json_path": str(stale_json)}]}), encoding="utf-8")
    _set_cfg(monkeypatch, post_dry_run=True)

    called = {"n": 0}
    fresh_dir = run_dir / "a"
    fresh_json = fresh_dir / "a.json"

    def _run_batch(payload, out_dir):
        called["n"] += 1
        fresh_dir.mkdir(parents=True, exist_ok=True)
        fresh_json.write_text("{}", encoding="utf-8")
        (run_dir / "summary.json").write_text(json.dumps({"items": [{"slug": "a", "json_path": str(fresh_json)}]}), encoding="utf-8")

    monkeypatch.setattr(autopost, "run_batch", _run_batch)
    monkeypatch.setattr(autopost, "load_reel_config", lambda p: object())
    monkeypatch.setattr(autopost, "render_reel", lambda cfg, out: Path(out).write_bytes(b"mp4"))
    monkeypatch.setattr(autopost, "publish_reel", lambda **k: {"instagram": {"status": "planned"}, "facebook": {"status": "planned"}, "video_url": "u"})

    result = autopost.run_autopost(_make_queue(tmp_path), "day_03", "https://example.trycloudflare.com", dry_run=True)
    assert called["n"] == 1
    assert result["items"][0]["json_path"] == str(fresh_json)


def test_autopost_stale_summary_missing_item_folder_no_render_fail(tmp_path, monkeypatch):
    monkeypatch.chdir(tmp_path)
    run_dir = tmp_path / "outputs/queue/day_03"
    run_dir.mkdir(parents=True)
    missing_item_json = run_dir / "missing/missing.json"
    (run_dir / "summary.json").write_text(json.dumps({"items": [{"slug": "missing", "json_path": str(missing_item_json)}]}), encoding="utf-8")
    _set_cfg(monkeypatch, post_dry_run=False)

    fresh_dir = run_dir / "a"
    fresh_json = fresh_dir / "a.json"

    def _run_batch(payload, out_dir):
        fresh_dir.mkdir(parents=True, exist_ok=True)
        fresh_json.write_text("{}", encoding="utf-8")
        (run_dir / "summary.json").write_text(json.dumps({"items": [{"slug": "a", "json_path": str(fresh_json)}]}), encoding="utf-8")

    monkeypatch.setattr(autopost, "run_batch", _run_batch)
    monkeypatch.setattr(autopost, "load_reel_config", lambda p: object())
    monkeypatch.setattr(autopost, "render_reel", lambda cfg, out: Path(out).write_bytes(b"mp4"))
    monkeypatch.setattr(autopost, "publish_reel", lambda **k: {"instagram": {"status": "success"}, "facebook": {"status": "success"}})

    result = autopost.run_autopost(_make_queue(tmp_path), "day_03", "https://example.trycloudflare.com", dry_run=False)
    assert result["items"][0].get("status") != "render_failed"


def test_autopost_dry_run_stale_summary_regenerates_without_cleanup_or_real_post(tmp_path, monkeypatch):
    monkeypatch.chdir(tmp_path)
    run_dir = tmp_path / "outputs/queue/day_03"
    run_dir.mkdir(parents=True)
    missing_json = run_dir / "a/a.json"
    (run_dir / "summary.json").write_text(json.dumps({"items": [{"slug": "a", "json_path": str(missing_json)}]}), encoding="utf-8")
    _set_cfg(monkeypatch, post_dry_run=True)

    fresh_dir = run_dir / "a"
    fresh_json = fresh_dir / "a.json"
    (fresh_dir / "a.wav").parent.mkdir(parents=True, exist_ok=True)
    (fresh_dir / "a.wav").write_bytes(b"wav")
    called = {"dry_run": None}

    def _run_batch(payload, out_dir):
        fresh_dir.mkdir(parents=True, exist_ok=True)
        fresh_json.write_text("{}", encoding="utf-8")
        (run_dir / "summary.json").write_text(json.dumps({"items": [{"slug": "a", "json_path": str(fresh_json)}]}), encoding="utf-8")

    def _publish(**kwargs):
        called["dry_run"] = kwargs["dry_run"]
        return {"instagram": {"status": "planned"}, "facebook": {"status": "planned"}, "video_url": "u"}

    monkeypatch.setattr(autopost, "run_batch", _run_batch)
    monkeypatch.setattr(autopost, "load_reel_config", lambda p: object())
    monkeypatch.setattr(autopost, "render_reel", lambda cfg, out: Path(out).write_bytes(b"mp4"))
    monkeypatch.setattr(autopost, "publish_reel", _publish)

    autopost.run_autopost(_make_queue(tmp_path), "day_03", "https://example.trycloudflare.com", dry_run=True)
    assert called["dry_run"] is True
    assert (fresh_dir / "a.wav").exists()
