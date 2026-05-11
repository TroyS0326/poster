import json
from types import SimpleNamespace

import scheduler


def _logger(calls=None):
    calls = calls if calls is not None else {}
    return SimpleNamespace(
        info=lambda *a, **k: None,
        warning=lambda *a, **k: calls.__setitem__("warning", calls.get("warning", 0) + 1),
        error=lambda *a, **k: None,
        exception=lambda *a, **k: None,
    )


def _cfg(tmp_path):
    return SimpleNamespace(
        max_generation_attempts=1,
        manual_review_mode=True,
        dry_run=True,
        prefer_local_public_image_url=False,
        log_path=str(tmp_path / "workflow.log"),
    )


def test_save_caption_history_trims_to_last_50(tmp_path):
    path = tmp_path / "caption_history.json"
    hashes = [f"h{i}" for i in range(75)]
    scheduler._save_caption_history(str(path), hashes, _logger())
    saved = json.loads(path.read_text(encoding="utf-8"))
    assert len(saved) == 50
    assert saved == hashes[-50:]


def test_load_caption_history_last_50_and_missing_file(tmp_path):
    cfg = SimpleNamespace(log_path=str(tmp_path / "run.log"))
    logger = _logger()

    missing_path, missing = scheduler._load_caption_history(cfg, logger)
    assert missing == []
    assert missing_path.endswith("caption_history.json")

    path = tmp_path / "caption_history.json"
    data = [f"h{i}" for i in range(70)]
    path.write_text(json.dumps(data), encoding="utf-8")
    loaded_path, loaded = scheduler._load_caption_history(cfg, logger)
    assert loaded_path == str(path)
    assert loaded == data[-50:]


def test_duplicate_guard_regenerates_and_saves_unique_hash(tmp_path, monkeypatch):
    cfg = _cfg(tmp_path)
    logger = _logger()
    history_path = tmp_path / "caption_history.json"
    dup = "duplicate caption"
    uniq = "unique caption"
    history_path.write_text(json.dumps([scheduler._caption_hash(dup)]), encoding="utf-8")

    build_calls = {"n": 0}

    def fake_build(*_args, **_kwargs):
        build_calls["n"] += 1
        return dup if build_calls["n"] == 1 else uniq

    monkeypatch.setattr(scheduler, "generate_content_package", lambda *_: {"caption": "raw", "image_prompt": "safe", "negative_prompt": "", "pillar": "risk", "archetype": "checklist"})
    monkeypatch.setattr(scheduler, "build_caption", fake_build)
    monkeypatch.setattr(scheduler, "validate_caption", lambda *_: (True, "ok"))
    monkeypatch.setattr(scheduler, "validate_image_prompt", lambda *_: (True, "ok"))
    monkeypatch.setattr(scheduler, "generate_image", lambda *_: {"local_path": "images/generated/a.jpg", "remote_url": "https://replicate.delivery/x.jpg"})
    monkeypatch.setattr(scheduler, "upload_image", lambda *_: "https://local.host/images/generated/a.jpg")
    monkeypatch.setattr(scheduler, "post_to_meta", lambda *_: {"facebook": {"status": "skipped"}, "instagram": {"status": "skipped"}})
    monkeypatch.setattr(scheduler, "run_preflight", lambda: {"fb_page_id": "valid", "ig_business_id": "valid"})

    scheduler.run_workflow(cfg, logger)

    assert build_calls["n"] >= 2
    saved = json.loads(history_path.read_text(encoding="utf-8"))
    assert scheduler._caption_hash(uniq) in saved


def test_corrupt_caption_history_does_not_fail_workflow(tmp_path, monkeypatch):
    calls = {}
    logger = _logger(calls)
    cfg = _cfg(tmp_path)
    (tmp_path / "caption_history.json").write_text("{invalid", encoding="utf-8")

    monkeypatch.setattr(scheduler, "generate_content_package", lambda *_: {"caption": "raw", "image_prompt": "safe", "negative_prompt": "", "pillar": "risk", "archetype": "checklist"})
    monkeypatch.setattr(scheduler, "validate_caption", lambda *_: (True, "ok"))
    monkeypatch.setattr(scheduler, "validate_image_prompt", lambda *_: (True, "ok"))
    monkeypatch.setattr(scheduler, "generate_image", lambda *_: {"local_path": "images/generated/a.jpg", "remote_url": "https://replicate.delivery/x.jpg"})
    monkeypatch.setattr(scheduler, "upload_image", lambda *_: "https://local.host/images/generated/a.jpg")
    monkeypatch.setattr(scheduler, "post_to_meta", lambda *_: {"facebook": {"status": "skipped"}, "instagram": {"status": "skipped"}})

    scheduler.run_workflow(cfg, logger)
    assert calls.get("warning", 0) >= 1


def test_scheduler_does_not_record_angle_on_image_failure(tmp_path, monkeypatch):
    cfg = _cfg(tmp_path)
    logger = _logger()
    monkeypatch.setattr(scheduler, "generate_content_package", lambda *_: {"caption": "raw", "image_prompt": "safe", "negative_prompt": "", "pillar": "risk", "archetype": "checklist", "visual_direction": "template:ui"})
    monkeypatch.setattr(scheduler, "build_caption", lambda *_args, **_kwargs: "ok caption")
    monkeypatch.setattr(scheduler, "validate_caption", lambda *_: (True, "ok"))
    monkeypatch.setattr(scheduler, "validate_image_prompt", lambda *_: (True, "ok"))
    monkeypatch.setattr(scheduler, "generate_image", lambda *_: None)
    scheduler.run_workflow(cfg, logger)
    assert not (tmp_path / "content_angle_history.json").exists()


def test_scheduler_records_angle_after_manual_review_success(tmp_path, monkeypatch):
    cfg = _cfg(tmp_path)
    logger = _logger()
    monkeypatch.setattr(scheduler, "generate_content_package", lambda *_: {"caption": "raw", "image_prompt": "safe", "negative_prompt": "", "pillar": "risk", "archetype": "checklist", "visual_direction": "template:ui"})
    monkeypatch.setattr(scheduler, "build_caption", lambda *_args, **_kwargs: "ok caption")
    monkeypatch.setattr(scheduler, "validate_caption", lambda *_: (True, "ok"))
    monkeypatch.setattr(scheduler, "validate_image_prompt", lambda *_: (True, "ok"))
    monkeypatch.setattr(scheduler, "generate_image", lambda *_: {"local_path": "images/generated/a.jpg", "remote_url": "https://replicate.delivery/x.jpg"})
    scheduler.run_workflow(cfg, logger)
    assert (tmp_path / "content_angle_history.json").exists()


def test_live_posting_all_fail_does_not_record_angle(tmp_path, monkeypatch):
    cfg = _cfg(tmp_path)
    cfg.manual_review_mode = False
    cfg.dry_run = False
    logger = _logger()
    monkeypatch.setattr(scheduler, "run_preflight", lambda: {"fb_page_id": "valid", "ig_business_id": "valid"})
    monkeypatch.setattr(scheduler, "generate_content_package", lambda *_: {"caption": "raw", "image_prompt": "safe", "negative_prompt": "", "pillar": "risk", "archetype": "checklist", "visual_direction": "template:ui"})
    monkeypatch.setattr(scheduler, "build_caption", lambda *_args, **_kwargs: "ok caption")
    monkeypatch.setattr(scheduler, "validate_caption", lambda *_: (True, "ok"))
    monkeypatch.setattr(scheduler, "validate_image_prompt", lambda *_: (True, "ok"))
    monkeypatch.setattr(scheduler, "generate_image", lambda *_: {"local_path": "images/generated/a.jpg", "remote_url": "https://replicate.delivery/x.jpg"})
    monkeypatch.setattr(scheduler, "post_to_meta", lambda *_: {"facebook": {"status": "failed"}, "instagram": {"status": "failed"}})
    scheduler.run_workflow(cfg, logger)
    assert not (tmp_path / "content_angle_history.json").exists()


def test_live_posting_partial_success_records_angle(tmp_path, monkeypatch):
    cfg = _cfg(tmp_path)
    cfg.manual_review_mode = False
    cfg.dry_run = False
    logger = _logger()
    monkeypatch.setattr(scheduler, "run_preflight", lambda: {"fb_page_id": "valid", "ig_business_id": "valid"})
    monkeypatch.setattr(scheduler, "generate_content_package", lambda *_: {"caption": "raw", "image_prompt": "safe", "negative_prompt": "", "pillar": "risk", "archetype": "checklist", "visual_direction": "template:ui"})
    monkeypatch.setattr(scheduler, "build_caption", lambda *_args, **_kwargs: "ok caption")
    monkeypatch.setattr(scheduler, "validate_caption", lambda *_: (True, "ok"))
    monkeypatch.setattr(scheduler, "validate_image_prompt", lambda *_: (True, "ok"))
    monkeypatch.setattr(scheduler, "generate_image", lambda *_: {"local_path": "images/generated/a.jpg", "remote_url": "https://replicate.delivery/x.jpg"})
    monkeypatch.setattr(scheduler, "post_to_meta", lambda *_: {"facebook": {"status": "success"}, "instagram": {"status": "failed"}})
    scheduler.run_workflow(cfg, logger)
    assert (tmp_path / "content_angle_history.json").exists()
