from types import SimpleNamespace

import main
import post_once
import text_ai


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


def test_template_p8_uses_approved_image_prompt(monkeypatch):
    cfg = SimpleNamespace(gemini_model="gemini-1.5-flash", gemini_api_key="k")
    logger = SimpleNamespace(info=lambda *a, **k: None, warning=lambda *a, **k: None)

    monkeypatch.setattr(text_ai.random, "choice", lambda seq: "template:p8" if seq == text_ai.VISUAL_DIRECTIONS else seq[0])
    monkeypatch.setattr(text_ai.random, "randint", lambda *_: 1111)
    monkeypatch.setattr(text_ai.time, "time", lambda: 1234567890)

    payload = {
        "candidates": [{
            "content": {"parts": [{"text": "{\"pillar\":\"p\",\"archetype\":\"a\",\"caption\":\"A compliant caption with enough words to exceed minimum threshold requirements for validation and clean structure in final output formatting.\",\"image_concept\":\"concept\",\"image_prompt\":\"unsafe rewritten prompt\",\"negative_prompt\":\"none\"}"}]}
        }]
    }

    class Resp:
        def raise_for_status(self): return None
        def json(self): return payload

    monkeypatch.setattr(text_ai.requests, "post", lambda *a, **k: Resp())
    package = text_ai.generate_content_package(cfg, logger)
    p8 = next(t["prompt"] for t in text_ai.IMAGE_PROMPT_TEMPLATES if t["id"] == "p8")
    assert package["image_prompt"] == p8
