import json
from types import SimpleNamespace

import scheduler
import text_ai


def _logger(calls=None):
    calls = calls if calls is not None else {}
    return SimpleNamespace(
        info=lambda *a, **k: None,
        warning=lambda *a, **k: calls.__setitem__("warning", calls.get("warning", 0) + 1),
        error=lambda *a, **k: None,
        exception=lambda *a, **k: None,
    )


def test_content_history_path_next_to_log_path(tmp_path):
    cfg = SimpleNamespace(log_path=str(tmp_path / "app.log"))
    assert text_ai._content_history_path(cfg) == str(tmp_path / "content_angle_history.json")


def test_load_save_content_angle_history(tmp_path):
    cfg = SimpleNamespace(log_path=str(tmp_path / "app.log"))
    logger = _logger()
    assert text_ai._load_content_angle_history(cfg, logger) == []

    path = text_ai._content_history_path(cfg)
    (tmp_path / "content_angle_history.json").write_text("{bad", encoding="utf-8")
    assert text_ai._load_content_angle_history(cfg, logger) == []

    history = [{"pillar": str(i), "archetype": "a", "visual_direction": "v", "created_at": i} for i in range(40)]
    text_ai._save_content_angle_history(path, history, logger)
    saved = json.loads((tmp_path / "content_angle_history.json").read_text(encoding="utf-8"))
    assert len(saved) == 30
    assert saved == history[-30:]


def test_malformed_history_schema_logs_warning_and_returns_empty(tmp_path):
    cfg = SimpleNamespace(log_path=str(tmp_path / "app.log"))
    calls = {}
    logger = _logger(calls)
    (tmp_path / "content_angle_history.json").write_text(json.dumps(["bad", 123, {"pillar": "", "archetype": "x", "visual_direction": "v"}]), encoding="utf-8")
    loaded = text_ai._load_content_angle_history(cfg, logger)
    assert loaded == []
    assert calls.get("warning", 0) >= 1
    sel = text_ai._select_content_angle(["bad", 123, {"pillar": "", "archetype": "x", "visual_direction": "v"}], seed=9)
    assert sel["pillar"] in text_ai.CONTENT_PILLARS


def test_mixed_valid_invalid_history_returns_only_valid_trimmed(tmp_path):
    cfg = SimpleNamespace(log_path=str(tmp_path / "app.log"))
    logger = _logger()
    valid = [{"pillar": f"p{i}", "archetype": "a", "visual_direction": "v", "created_at": i} for i in range(35)]
    mixed = ["bad", {"pillar": "", "archetype": "a", "visual_direction": "v"}] + valid
    (tmp_path / "content_angle_history.json").write_text(json.dumps(mixed), encoding="utf-8")
    loaded = text_ai._load_content_angle_history(cfg, logger)
    assert len(loaded) == 30
    assert loaded == valid[-30:]


def test_select_content_angle_cooldowns_and_relaxation():
    p0, p1 = text_ai.CONTENT_PILLARS[0], text_ai.CONTENT_PILLARS[1]
    a0, a1 = text_ai.POST_ARCHETYPES[0], text_ai.POST_ARCHETYPES[1]
    v0, v1 = text_ai.VISUAL_DIRECTIONS[0], text_ai.VISUAL_DIRECTIONS[1]

    hist = [
        {"pillar": p0, "archetype": a1, "visual_direction": v1},
        {"pillar": p0, "archetype": a1, "visual_direction": v1},
        {"pillar": p0, "archetype": a1, "visual_direction": v1},
    ]
    sel = text_ai._select_content_angle(hist, seed=1)
    assert sel["pillar"] != p0

    hist2 = [{"pillar": p1, "archetype": a0, "visual_direction": v1}, {"pillar": p1, "archetype": a0, "visual_direction": v1}]
    sel2 = text_ai._select_content_angle(hist2, seed=2)
    assert sel2["archetype"] != a0

    hist3 = [{"pillar": p1, "archetype": a1, "visual_direction": v0}, {"pillar": p1, "archetype": a1, "visual_direction": v0}]
    sel3 = text_ai._select_content_angle(hist3, seed=3)
    assert sel3["visual_direction"] != v0

    hist4 = [{"pillar": p0, "archetype": a0, "visual_direction": v1} for _ in range(10)]
    sel4 = text_ai._select_content_angle(hist4, seed=4)
    assert (sel4["pillar"], sel4["archetype"]) != (p0, a0)

    impossible = [{"pillar": p, "archetype": a0, "visual_direction": v0} for p in text_ai.CONTENT_PILLARS[-3:]]
    sel5 = text_ai._select_content_angle(impossible, seed=5)
    assert sel5["pillar"] in text_ai.CONTENT_PILLARS
    assert sel5["archetype"] in text_ai.POST_ARCHETYPES
    assert sel5["visual_direction"] in text_ai.VISUAL_DIRECTIONS


def test_generate_content_package_fallback_includes_angle_metadata(monkeypatch):
    cfg = SimpleNamespace(log_path="logs/app.log", gemini_model="g", gemini_api_key="k")
    logger = _logger()

    def boom(*_args, **_kwargs):
        raise text_ai.requests.RequestException("down")

    monkeypatch.setattr(text_ai.requests, "post", boom)
    package = text_ai.generate_content_package(cfg, logger)
    assert package["pillar"]
    assert package["archetype"]
    assert package["visual_direction"]
    assert package["caption"]


def test_fallback_template_visual_direction_sets_matching_prompt(monkeypatch):
    cfg = SimpleNamespace(log_path="logs/app.log", gemini_model="g", gemini_api_key="k")
    logger = _logger()
    monkeypatch.setattr(text_ai, "_select_content_angle", lambda *_args, **_kwargs: {"pillar": "p", "archetype": "a", "visual_direction": "template:p1"})

    def boom(*_args, **_kwargs):
        raise text_ai.requests.RequestException("down")

    monkeypatch.setattr(text_ai.requests, "post", boom)
    package = text_ai.generate_content_package(cfg, logger)
    template = next(t for t in text_ai.IMAGE_PROMPT_TEMPLATES if t["id"] == "p1")
    assert package["visual_direction"] == "template:p1"
    assert package["image_prompt"] == template["prompt"]


def test_scheduler_persists_content_angle_history(tmp_path, monkeypatch):
    cfg = SimpleNamespace(
        max_generation_attempts=1,
        manual_review_mode=True,
        dry_run=True,
        prefer_local_public_image_url=False,
        log_path=str(tmp_path / "workflow.log"),
    )
    logger = _logger()

    monkeypatch.setattr(scheduler, "generate_content_package", lambda *_: {"caption": "raw", "image_prompt": "safe", "negative_prompt": "", "pillar": "risk", "archetype": "checklist", "visual_direction": "template:ui"})
    monkeypatch.setattr(scheduler, "build_caption", lambda *_args, **_kwargs: "ok caption")
    monkeypatch.setattr(scheduler, "validate_caption", lambda *_: (True, "ok"))
    monkeypatch.setattr(scheduler, "validate_image_prompt", lambda *_: (True, "ok"))
    monkeypatch.setattr(scheduler, "generate_image", lambda *_: {"local_path": "images/generated/a.jpg", "remote_url": "https://replicate.delivery/x.jpg"})
    monkeypatch.setattr(scheduler, "upload_image", lambda *_: "https://local.host/images/generated/a.jpg")
    monkeypatch.setattr(scheduler, "post_to_meta", lambda *_: {"facebook": {"status": "skipped"}, "instagram": {"status": "skipped"}})

    scheduler.run_workflow(cfg, logger)
    content_path = tmp_path / "content_angle_history.json"
    assert content_path.exists()
    history = json.loads(content_path.read_text(encoding="utf-8"))
    assert history[-1]["pillar"] == "risk"
    assert history[-1]["archetype"] == "checklist"

    content_path.unlink()
    monkeypatch.setattr(scheduler, "validate_caption", lambda *_: (False, "bad"))
    scheduler.run_workflow(cfg, logger)
    assert not content_path.exists()
