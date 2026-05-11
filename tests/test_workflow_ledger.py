import json
from pathlib import Path
from types import SimpleNamespace

import scheduler


class _Logger:
    def __init__(self):
        self.warning_calls = []

    def info(self, *_):
        return None

    def warning(self, msg, *args):
        self.warning_calls.append(msg % args if args else msg)

    def error(self, *_):
        return None

    def exception(self, *_):
        return None


def _cfg(tmp_path, **overrides):
    base = dict(
        max_generation_attempts=1,
        manual_review_mode=True,
        dry_run=True,
        prefer_local_public_image_url=False,
        log_path=str(tmp_path / "logs" / "app.log"),
    )
    base.update(overrides)
    return SimpleNamespace(**base)


def _base_monkeypatch(monkeypatch):
    monkeypatch.setattr(scheduler, "generate_content_package", lambda *_: {"caption": "raw", "image_prompt": "safe", "negative_prompt": "none", "pillar": "risk", "archetype": "checklist", "visual_direction": "template:ui"})
    monkeypatch.setattr(scheduler, "build_caption", lambda *_args, **_kwargs: "Great post body\n#alpha #beta #gamma #delta")
    monkeypatch.setattr(scheduler, "validate_caption", lambda *_: (True, "ok"))
    monkeypatch.setattr(scheduler, "validate_image_prompt", lambda *_: (True, "ok"))
    monkeypatch.setattr(scheduler, "generate_image", lambda *_: {"local_path": "images/generated/a.jpg", "remote_url": "https://replicate.delivery/x.jpg"})
    monkeypatch.setattr(scheduler, "upload_image", lambda *_: "https://local.host/images/generated/a.jpg")


def _read_ledger(path: Path):
    lines = path.read_text(encoding="utf-8").strip().splitlines()
    return [json.loads(x) for x in lines if x.strip()]


def test_workflow_ledger_path_next_to_log_path(tmp_path):
    cfg = _cfg(tmp_path)
    assert scheduler._workflow_ledger_path(cfg) == str(tmp_path / "logs" / "workflow_runs.jsonl")


def test_append_workflow_ledger_jsonl(tmp_path):
    cfg = _cfg(tmp_path)
    logger = _Logger()
    scheduler._append_workflow_ledger(cfg, logger, {"a": 1})
    scheduler._append_workflow_ledger(cfg, logger, {"b": 2})
    ledger = Path(scheduler._workflow_ledger_path(cfg))
    lines = ledger.read_text(encoding="utf-8").splitlines()
    assert len(lines) == 2
    assert json.loads(lines[0])["a"] == 1
    assert json.loads(lines[1])["b"] == 2


def test_manual_review_records_ledger_and_histories(tmp_path, monkeypatch):
    cfg = _cfg(tmp_path, manual_review_mode=True, dry_run=False)
    logger = _Logger()
    _base_monkeypatch(monkeypatch)

    scheduler.run_workflow(cfg, logger)

    row = _read_ledger(Path(scheduler._workflow_ledger_path(cfg)))[0]
    assert row["outcome"] == "manual_review_ready"
    assert row["pillar"] == "risk"
    assert row["archetype"] == "checklist"
    assert row["visual_direction"] == "template:ui"
    assert row["caption_hash"]
    assert row["hosted_url"]
    assert (tmp_path / "logs" / "content_angle_history.json").exists()


def test_image_generation_failure_records_ledger_not_histories(tmp_path, monkeypatch):
    cfg = _cfg(tmp_path)
    logger = _Logger()
    _base_monkeypatch(monkeypatch)
    monkeypatch.setattr(scheduler, "generate_image", lambda *_: None)

    scheduler.run_workflow(cfg, logger)

    row = _read_ledger(Path(scheduler._workflow_ledger_path(cfg)))[0]
    assert row["outcome"] == "skipped_image_failed"
    assert not (tmp_path / "logs" / "content_angle_history.json").exists()
    assert not (tmp_path / "logs" / "caption_history.json").exists()


def test_validation_failure_records_ledger_not_history(tmp_path, monkeypatch):
    cfg = _cfg(tmp_path)
    logger = _Logger()
    _base_monkeypatch(monkeypatch)
    monkeypatch.setattr(scheduler, "validate_caption", lambda *_: (False, "caption failure"))

    scheduler.run_workflow(cfg, logger)

    row = _read_ledger(Path(scheduler._workflow_ledger_path(cfg)))[0]
    assert row["outcome"] == "skipped_validation_failed"
    assert "caption failure" in (row["failure_reason"] or "")
    assert not (tmp_path / "logs" / "content_angle_history.json").exists()


def test_live_posting_all_fail_records_failed_outcome(tmp_path, monkeypatch):
    cfg = _cfg(tmp_path, manual_review_mode=False, dry_run=False)
    logger = _Logger()
    _base_monkeypatch(monkeypatch)
    monkeypatch.setattr(scheduler, "run_preflight", lambda: {"fb_page_id": "valid", "ig_business_id": "valid"})
    monkeypatch.setattr(scheduler, "post_to_meta", lambda *_: {"facebook": {"status": "failed", "error": "fb"}, "instagram": {"status": "failed", "error": "ig"}})

    scheduler.run_workflow(cfg, logger)

    row = _read_ledger(Path(scheduler._workflow_ledger_path(cfg)))[0]
    assert row["outcome"] == "posted_failed"
    assert not (tmp_path / "logs" / "content_angle_history.json").exists()


def test_live_partial_success_records_partial_and_history(tmp_path, monkeypatch):
    cfg = _cfg(tmp_path, manual_review_mode=False, dry_run=False)
    logger = _Logger()
    _base_monkeypatch(monkeypatch)
    monkeypatch.setattr(scheduler, "run_preflight", lambda: {"fb_page_id": "valid", "ig_business_id": "valid"})
    monkeypatch.setattr(scheduler, "post_to_meta", lambda *_: {"facebook": {"status": "success", "id": "1"}, "instagram": {"status": "failed", "error": "ig"}})

    scheduler.run_workflow(cfg, logger)

    row = _read_ledger(Path(scheduler._workflow_ledger_path(cfg)))[0]
    assert row["outcome"] == "posted_partial_success"
    assert (tmp_path / "logs" / "content_angle_history.json").exists()


def test_ledger_write_failure_warns_and_workflow_continues(tmp_path, monkeypatch):
    cfg = _cfg(tmp_path)
    logger = _Logger()
    _base_monkeypatch(monkeypatch)
    monkeypatch.setattr(scheduler, "_append_workflow_ledger", lambda *_: (_ for _ in ()).throw(OSError("disk full")))

    # make wrapper catch failure by monkeypatching to original failure path through open
    def safe_append(config, log, entry):
        try:
            raise OSError("disk full")
        except Exception as exc:
            log.warning("workflow ledger append failed: %s", exc)

    monkeypatch.setattr(scheduler, "_append_workflow_ledger", safe_append)
    scheduler.run_workflow(cfg, logger)

    assert any("workflow ledger append failed" in m for m in logger.warning_calls)
    assert (tmp_path / "logs" / "content_angle_history.json").exists()
