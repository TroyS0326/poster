from types import SimpleNamespace

import main
import post_once


def test_post_once_calls_run_workflow_once(monkeypatch):
    calls = {"run": 0, "schedule": 0}
    cfg = SimpleNamespace(log_path="logs/x.log")

    monkeypatch.setattr(post_once, "load_config", lambda: cfg)
    monkeypatch.setattr(post_once, "validate_required_config", lambda *_: (True, []))
    monkeypatch.setattr(post_once, "setup_logger", lambda *_: SimpleNamespace(info=lambda *a, **k: None, error=lambda *a, **k: None))
    monkeypatch.setattr(post_once, "run_workflow", lambda *_: calls.__setitem__("run", calls["run"] + 1))
    monkeypatch.setattr(main, "schedule_posts", lambda *_: calls.__setitem__("schedule", calls["schedule"] + 1))

    post_once.main()

    assert calls["run"] == 1
    assert calls["schedule"] == 0


def test_main_uses_schedule_posts_entrypoint(monkeypatch):
    calls = {"schedule": 0, "run": 0}
    cfg = SimpleNamespace(log_path="logs/x.log", post_interval_hours=4)

    monkeypatch.setattr(main, "load_config", lambda: cfg)
    monkeypatch.setattr(main, "validate_required_config", lambda *_: (True, []))
    monkeypatch.setattr(main, "setup_logger", lambda *_: SimpleNamespace(info=lambda *a, **k: None, error=lambda *a, **k: None))
    monkeypatch.setattr(main, "schedule_posts", lambda *_: calls.__setitem__("schedule", calls["schedule"] + 1))
    monkeypatch.setattr(post_once, "run_workflow", lambda *_: calls.__setitem__("run", calls["run"] + 1))

    main.main()

    assert calls["schedule"] == 1
    assert calls["run"] == 0
