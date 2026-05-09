import json
from pathlib import Path

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


def test_autopost_dry_run_limit3_deletes_nothing(tmp_path, monkeypatch):
    monkeypatch.chdir(tmp_path)
    run_dir = tmp_path / "outputs/queue/day_03"
    run_dir.mkdir(parents=True)
    items = []
    for slug in ["a", "b", "c", "d"]:
        d = run_dir / slug
        d.mkdir()
        (d / f"{slug}.json").write_text("{}", encoding="utf-8")
        (d / f"{slug}.mp4").write_bytes(b"mp4")
        (d / f"{slug}.wav").write_bytes(b"wav")
        items.append({"slug": slug, "json_path": str(d / f"{slug}.json"), "mp4_path": str(d / f"{slug}.mp4")})
    (run_dir / "summary.json").write_text(json.dumps({"items": items}), encoding="utf-8")
    monkeypatch.setattr(autopost, "publish_reel", lambda **k: {"instagram": {"status": "planned"}, "facebook": {"status": "planned"}, "video_url": "u"})

    result = autopost.run_autopost(_make_queue(tmp_path), "day_03", "https://example.trycloudflare.com", limit=3, dry_run=True)
    assert result["processed"] == 3
    assert (run_dir / "a/a.mp4").exists()
    assert (run_dir / "publish_summary.json").exists()
    assert (run_dir / "publish_events.jsonl").exists()


def test_autopost_success_cleanup(tmp_path, monkeypatch):
    monkeypatch.chdir(tmp_path)
    run_dir = tmp_path / "outputs/queue/day_03/a"
    run_dir.mkdir(parents=True)
    (run_dir / "a.json").write_text("{}", encoding="utf-8")
    (run_dir / "a.mp4").write_bytes(b"mp4")
    (run_dir / "a.wav").write_bytes(b"wav")
    (run_dir / "a.png").write_bytes(b"png")
    (run_dir / "run_report.md").write_text("r", encoding="utf-8")
    parent = run_dir.parent
    (parent / "summary.json").write_text(json.dumps({"items": [{"slug": "a", "json_path": str(run_dir / 'a.json'), "mp4_path": str(run_dir / 'a.mp4')}]}), encoding="utf-8")
    monkeypatch.setattr(autopost, "publish_reel", lambda **k: {"instagram": {"status": "success"}, "facebook": {"status": "success"}})

    autopost.run_autopost(_make_queue(tmp_path), "day_03", "https://example.trycloudflare.com", limit=3, dry_run=False)
    assert not (run_dir / "a.mp4").exists()
    assert not (run_dir / "a.wav").exists()
    assert not (run_dir / "a.png").exists()
    assert (run_dir / "a.json").exists()
    assert (run_dir / "run_report.md").exists()


def test_autopost_failed_publish_keeps_files(tmp_path, monkeypatch):
    monkeypatch.chdir(tmp_path)
    run_dir = tmp_path / "outputs/queue/day_03/a"
    run_dir.mkdir(parents=True)
    (run_dir / "a.json").write_text("{}", encoding="utf-8")
    (run_dir / "a.mp4").write_bytes(b"mp4")
    (run_dir.parent / "summary.json").write_text(json.dumps({"items": [{"slug": "a", "json_path": str(run_dir / 'a.json'), "mp4_path": str(run_dir / 'a.mp4')}]}), encoding="utf-8")
    monkeypatch.setattr(autopost, "publish_reel", lambda **k: {"instagram": {"status": "success"}, "facebook": {"status": "failed"}})

    autopost.run_autopost(_make_queue(tmp_path), "day_03", "https://example.trycloudflare.com", dry_run=False)
    assert (run_dir / "a.mp4").exists()
