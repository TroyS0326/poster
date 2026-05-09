import json
from pathlib import Path

from reels import scheduler


def _queue(tmp_path: Path, *, first_slug: str = "a"):
    q = tmp_path / "q.json"
    q.write_text(
        json.dumps(
            {
                "output_root": "outputs/queue",
                "runs": [
                    {
                        "run_id": "day_01",
                        "items": [
                            {"topic": "A Topic", "slug": first_slug},
                            {"topic": "B Topic", "slug": "b"},
                        ],
                    }
                ],
            }
        ),
        encoding="utf-8",
    )
    return q


def _load_state(tmp_path: Path) -> dict:
    state_path = tmp_path / "outputs" / "reels_scheduler_state.json"
    return json.loads(state_path.read_text(encoding="utf-8"))


def test_once_processes_one_item(tmp_path, monkeypatch):
    monkeypatch.chdir(tmp_path)
    calls = []

    def _auto(*args, **kwargs):
        calls.append(kwargs.get("limit"))
        return {"platform": "instagram", "items": [{"publish": {"instagram": {"status": "planned"}}}]}

    monkeypatch.setattr(scheduler, "run_autopost", _auto)
    scheduler.run_scheduler(_queue(tmp_path), "https://x", once=True, dry_run=True)
    assert calls == [1]


def test_dry_run_once_does_not_mark_posted(tmp_path, monkeypatch):
    monkeypatch.chdir(tmp_path)
    monkeypatch.setattr(
        scheduler,
        "run_autopost",
        lambda *args, **kwargs: {"platform": "instagram", "items": [{"publish": {"instagram": {"status": "planned"}}}]},
    )

    scheduler.run_scheduler(_queue(tmp_path), "https://x", once=True, dry_run=True)
    state = _load_state(tmp_path)
    assert state.get("posted", {}) == {}


def test_dry_run_twice_selects_same_item(tmp_path, monkeypatch):
    monkeypatch.chdir(tmp_path)
    selected = []

    def _auto(*args, **kwargs):
        selected.append(args[1])
        return {"platform": "instagram", "items": [{"publish": {"instagram": {"status": "planned"}}}]}

    monkeypatch.setattr(scheduler, "run_autopost", _auto)
    q = _queue(tmp_path)

    first = scheduler.run_scheduler(q, "https://x", once=True, dry_run=True)
    second = scheduler.run_scheduler(q, "https://x", once=True, dry_run=True)

    assert first["slug"] == "a"
    assert second["slug"] == "a"
    assert selected == ["day_01", "day_01"]


def test_real_success_marks_posted(tmp_path, monkeypatch):
    monkeypatch.chdir(tmp_path)
    monkeypatch.setattr(
        scheduler,
        "run_autopost",
        lambda *args, **kwargs: {"platform": "both", "items": [{"publish": {"instagram": {"status": "success"}, "facebook": {"status": "success"}}}]},
    )

    scheduler.run_scheduler(_queue(tmp_path), "https://x", once=True, dry_run=False)
    state = _load_state(tmp_path)
    assert "day_01:a" in state.get("posted", {})
    assert "day_01:a" not in state.get("failed", {})


def test_real_failed_publish_marks_failed_not_posted(tmp_path, monkeypatch):
    monkeypatch.chdir(tmp_path)
    monkeypatch.setattr(
        scheduler,
        "run_autopost",
        lambda *args, **kwargs: {"platform": "both", "items": [{"publish": {"instagram": {"status": "success"}, "facebook": {"status": "failed"}}}]},
    )

    scheduler.run_scheduler(_queue(tmp_path), "https://x", once=True, dry_run=False)
    state = _load_state(tmp_path)
    assert "day_01:a" not in state.get("posted", {})
    assert state.get("failed", {}).get("day_01:a", {}).get("platform") == "both"


def test_render_failed_marks_failed_not_posted(tmp_path, monkeypatch):
    monkeypatch.chdir(tmp_path)
    monkeypatch.setattr(
        scheduler,
        "run_autopost",
        lambda *args, **kwargs: {"platform": "instagram", "items": [{"status": "render_failed", "error": "boom"}]},
    )

    scheduler.run_scheduler(_queue(tmp_path), "https://x", once=True, dry_run=False)
    state = _load_state(tmp_path)
    assert "day_01:a" not in state.get("posted", {})
    assert state.get("failed", {}).get("day_01:a", {}).get("status") == "render_failed"


def test_real_success_then_second_once_moves_to_next_item(tmp_path, monkeypatch):
    monkeypatch.chdir(tmp_path)
    monkeypatch.setattr(
        scheduler,
        "run_autopost",
        lambda *args, **kwargs: {"platform": "instagram", "items": [{"publish": {"instagram": {"status": "success"}}}]},
    )

    q = _queue(tmp_path)
    first = scheduler.run_scheduler(q, "https://x", once=True, dry_run=False)
    second = scheduler.run_scheduler(q, "https://x", once=True, dry_run=False)

    assert first["slug"] == "a"
    assert second["slug"] == "b"


def test_scheduler_slug_uses_batch_slugify(tmp_path, monkeypatch):
    monkeypatch.chdir(tmp_path)
    monkeypatch.setattr(
        scheduler,
        "run_autopost",
        lambda *args, **kwargs: {"platform": "instagram", "items": [{"publish": {"instagram": {"status": "success"}}}]},
    )

    q = _queue(tmp_path, first_slug="Weird -- Slug!!!")
    scheduler.run_scheduler(q, "https://x", once=True, dry_run=False)
    state = _load_state(tmp_path)
    assert "day_01:weird_slug" in state.get("posted", {})


def test_interval_sleep_called(tmp_path, monkeypatch):
    monkeypatch.chdir(tmp_path)
    monkeypatch.setattr(
        scheduler,
        "run_autopost",
        lambda *args, **kwargs: {"platform": "instagram", "items": [{"publish": {"instagram": {"status": "planned"}}}]},
    )
    slept = {"v": None}
    monkeypatch.setattr(scheduler.time, "sleep", lambda v: slept.__setitem__("v", v) or (_ for _ in ()).throw(SystemExit()))
    try:
        scheduler.run_scheduler(_queue(tmp_path), "https://x", once=False, dry_run=True, interval_hours=0.01)
    except SystemExit:
        pass
    assert slept["v"] == 36.0
