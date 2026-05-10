from types import SimpleNamespace

import config as config_module
import scheduler


def _base_config(**overrides):
    values = dict(
        image_provider="replicate",
        sd_api_url="http://127.0.0.1:7860",
        replicate_api_token="token",
        replicate_model="model",
        replicate_output_format="jpg",
        meta_access_token="meta",
        fb_page_id="fb",
        ig_business_id="ig",
        img_public_url_base="",
        prefer_local_public_image_url=True,
        gemini_api_key="gem",
        gemini_model="gemini-1.5-flash",
        openai_api_key="",
        meta_graph_version="v20.0",
        post_interval_hours=4,
        randomize_interval_minutes=0,
        log_path="logs/x.log",
        dry_run=False,
        manual_review_mode=False,
        max_generation_attempts=1,
        image_width=1080,
        image_height=1350,
        sd_model="dreamshaper_8.safetensors",
    )
    values.update(overrides)
    return config_module.Config(**values)


def test_validate_required_config_requires_img_public_when_prefer_local_true():
    cfg = _base_config(img_public_url_base="", prefer_local_public_image_url=True)
    ok, missing = config_module.validate_required_config(cfg)
    assert not ok
    assert "IMG_PUBLIC_URL_BASE" in missing


def test_validate_required_config_replicate_allows_missing_img_public_when_prefer_local_false():
    cfg = _base_config(img_public_url_base="", prefer_local_public_image_url=False)
    ok, missing = config_module.validate_required_config(cfg)
    assert ok
    assert "IMG_PUBLIC_URL_BASE" not in missing


def test_scheduler_uses_upload_when_prefer_local_true(monkeypatch):
    cfg = SimpleNamespace(max_generation_attempts=1, manual_review_mode=False, dry_run=False, prefer_local_public_image_url=True)
    logger = SimpleNamespace(info=lambda *a, **k: None, warning=lambda *a, **k: None, error=lambda *a, **k: None, exception=lambda *a, **k: None)
    monkeypatch.setattr(scheduler, "generate_content_package", lambda *_: {"caption": "c", "image_prompt": "p", "negative_prompt": ""})
    monkeypatch.setattr(scheduler, "validate_caption", lambda *_: (True, "ok"))
    monkeypatch.setattr(scheduler, "validate_image_prompt", lambda *_: (True, "ok"))
    monkeypatch.setattr(scheduler, "generate_image", lambda *_: {"local_path": "images/generated/a.jpg", "remote_url": "https://replicate.delivery/x.jpg"})
    monkeypatch.setattr(scheduler, "upload_image", lambda *_: "https://local.host/images/generated/a.jpg")
    captured = {}
    def fake_post_to_meta(caption, hosted_url, *_):
        captured["url"] = hosted_url
        return {"facebook": {"status": "ok"}, "instagram": {"status": "ok"}}

    monkeypatch.setattr(scheduler, "post_to_meta", fake_post_to_meta)
    monkeypatch.setattr(scheduler, "run_preflight", lambda: {"fb_page_id": "valid", "ig_business_id": "valid"})

    scheduler.run_workflow(cfg, logger)
    assert captured["url"] == "https://local.host/images/generated/a.jpg"


def test_scheduler_uses_remote_when_prefer_local_false(monkeypatch):
    cfg = SimpleNamespace(max_generation_attempts=1, manual_review_mode=False, dry_run=False, prefer_local_public_image_url=False)
    logger = SimpleNamespace(info=lambda *a, **k: None, warning=lambda *a, **k: None, error=lambda *a, **k: None, exception=lambda *a, **k: None)
    monkeypatch.setattr(scheduler, "generate_content_package", lambda *_: {"caption": "c", "image_prompt": "p", "negative_prompt": ""})
    monkeypatch.setattr(scheduler, "validate_caption", lambda *_: (True, "ok"))
    monkeypatch.setattr(scheduler, "validate_image_prompt", lambda *_: (True, "ok"))
    monkeypatch.setattr(scheduler, "generate_image", lambda *_: {"local_path": "images/generated/a.jpg", "remote_url": "https://replicate.delivery/x.jpg"})
    monkeypatch.setattr(scheduler, "upload_image", lambda *_: "https://local.host/images/generated/a.jpg")
    captured = {}
    def fake_post_to_meta(caption, hosted_url, *_):
        captured["url"] = hosted_url
        return {"facebook": {"status": "ok"}, "instagram": {"status": "ok"}}

    monkeypatch.setattr(scheduler, "post_to_meta", fake_post_to_meta)
    monkeypatch.setattr(scheduler, "run_preflight", lambda: {"fb_page_id": "valid", "ig_business_id": "valid"})

    scheduler.run_workflow(cfg, logger)
    assert captured["url"] == "https://replicate.delivery/x.jpg"



def test_scheduler_sanitizes_before_validate_for_risk(monkeypatch):
    cfg = SimpleNamespace(max_generation_attempts=1, manual_review_mode=True, dry_run=True, prefer_local_public_image_url=False)
    logger = SimpleNamespace(info=lambda *a, **k: None, warning=lambda *a, **k: None, error=lambda *a, **k: None, exception=lambda *a, **k: None)

    candidate = {"caption": "Short note about live trading execution.", "image_prompt": "p", "negative_prompt": "", "pillar": "Risk controls", "archetype": "checklist"}
    monkeypatch.setattr(scheduler, "generate_content_package", lambda *_: candidate.copy())

    seen = {"caption": None}
    def fake_validate_caption(c):
        seen["caption"] = c
        return True, "ok"

    monkeypatch.setattr(scheduler, "validate_caption", fake_validate_caption)
    monkeypatch.setattr(scheduler, "validate_image_prompt", lambda *_: (True, "ok"))
    monkeypatch.setattr(scheduler, "generate_image", lambda *_: {"local_path": "images/generated/a.jpg", "remote_url": "https://replicate.delivery/x.jpg"})
    monkeypatch.setattr(scheduler, "upload_image", lambda *_: "https://local.host/images/generated/a.jpg")
    monkeypatch.setattr(scheduler, "post_to_meta", lambda *_: {"facebook": {"status": "skipped"}, "instagram": {"status": "skipped"}})

    scheduler.run_workflow(cfg, logger)
    assert seen["caption"] is not None
    assert "Not financial advice. Trading involves risk." in seen["caption"]


def test_scheduler_repairs_caption_before_validate(monkeypatch):
    cfg = SimpleNamespace(max_generation_attempts=1, manual_review_mode=True, dry_run=True, prefer_local_public_image_url=False)
    logger = SimpleNamespace(info=lambda *a, **k: None, warning=lambda *a, **k: None, error=lambda *a, **k: None, exception=lambda *a, **k: None)
    candidate = {
        "caption": "A risk-free system that can improve profit with signals and buy alert behavior.",
        "image_prompt": "Create a disciplined dark fintech dashboard with validation and execution workflow details, no unrealistic claims, ultra detailed 16:9",
        "negative_prompt": "",
        "pillar": "Risk controls",
        "archetype": "checklist",
    }
    monkeypatch.setattr(scheduler, "generate_content_package", lambda *_: candidate.copy())

    seen = {"caption": None}
    def fake_validate_caption(caption):
        seen["caption"] = caption
        return True, "ok"

    monkeypatch.setattr(scheduler, "validate_caption", fake_validate_caption)
    monkeypatch.setattr(scheduler, "validate_image_prompt", lambda *_: (True, "ok"))
    monkeypatch.setattr(scheduler, "generate_image", lambda *_: {"local_path": "images/generated/a.jpg", "remote_url": "https://replicate.delivery/x.jpg"})
    monkeypatch.setattr(scheduler, "upload_image", lambda *_: "https://local.host/images/generated/a.jpg")
    monkeypatch.setattr(scheduler, "post_to_meta", lambda *_: {"facebook": {"status": "skipped"}, "instagram": {"status": "skipped"}})

    scheduler.run_workflow(cfg, logger)
    assert seen["caption"] is not None
    lowered = seen["caption"].lower()
    assert "risk-free" not in lowered
    assert "profit" not in lowered


def test_scheduler_final_caption_has_no_dangling_visit(monkeypatch):
    cfg = SimpleNamespace(max_generation_attempts=1, manual_review_mode=True, dry_run=True, prefer_local_public_image_url=False)
    logger = SimpleNamespace(info=lambda *a, **k: None, warning=lambda *a, **k: None, error=lambda *a, **k: None, exception=lambda *a, **k: None)
    candidate = {"caption": "Workflow summary. Visit: .", "image_prompt": "p", "negative_prompt": "", "pillar": "Risk controls", "archetype": "checklist"}
    monkeypatch.setattr(scheduler, "generate_content_package", lambda *_: candidate.copy())
    seen = {"caption": None}
    monkeypatch.setattr(scheduler, "validate_caption", lambda c: (seen.__setitem__("caption", c) or True, "ok"))
    monkeypatch.setattr(scheduler, "validate_image_prompt", lambda *_: (True, "ok"))
    monkeypatch.setattr(scheduler, "generate_image", lambda *_: {"local_path": "images/generated/a.jpg", "remote_url": "https://replicate.delivery/x.jpg"})
    monkeypatch.setattr(scheduler, "upload_image", lambda *_: "https://local.host/images/generated/a.jpg")
    monkeypatch.setattr(scheduler, "post_to_meta", lambda *_: {"facebook": {"status": "skipped"}, "instagram": {"status": "skipped"}})
    scheduler.run_workflow(cfg, logger)
    assert "Visit:" not in seen["caption"]


def test_scheduler_final_caption_has_no_duplicate_disclosure_fragments(monkeypatch):
    cfg = SimpleNamespace(max_generation_attempts=1, manual_review_mode=True, dry_run=True, prefer_local_public_image_url=False)
    logger = SimpleNamespace(info=lambda *a, **k: None, warning=lambda *a, **k: None, error=lambda *a, **k: None, exception=lambda *a, **k: None)
    candidate = {
        "caption": "Live trading notes. Not financial advice. Trading involves risk. Trading involves risk.",
        "image_prompt": "p",
        "negative_prompt": "",
        "pillar": "Risk controls",
        "archetype": "checklist",
    }
    monkeypatch.setattr(scheduler, "generate_content_package", lambda *_: candidate.copy())
    seen = {"caption": None}
    monkeypatch.setattr(scheduler, "validate_caption", lambda c: (seen.__setitem__("caption", c) or True, "ok"))
    monkeypatch.setattr(scheduler, "validate_image_prompt", lambda *_: (True, "ok"))
    monkeypatch.setattr(scheduler, "generate_image", lambda *_: {"local_path": "images/generated/a.jpg", "remote_url": "https://replicate.delivery/x.jpg"})
    monkeypatch.setattr(scheduler, "upload_image", lambda *_: "https://local.host/images/generated/a.jpg")
    monkeypatch.setattr(scheduler, "post_to_meta", lambda *_: {"facebook": {"status": "skipped"}, "instagram": {"status": "skipped"}})
    scheduler.run_workflow(cfg, logger)
    lowered = seen["caption"].lower()
    assert lowered.count("trading involves risk") == 1
    assert lowered.count("not financial advice") == 1


def test_scheduler_final_caption_repaired_before_validate_has_no_overclaims(monkeypatch):
    cfg = SimpleNamespace(max_generation_attempts=1, manual_review_mode=True, dry_run=True, prefer_local_public_image_url=False)
    logger = SimpleNamespace(info=lambda *a, **k: None, warning=lambda *a, **k: None, error=lambda *a, **k: None, exception=lambda *a, **k: None)
    candidate = {
        "caption": "This engine ensures flawless execution while freeing you from emotional pitfalls and exploring smarter execution.",
        "image_prompt": "Create a disciplined dark fintech dashboard with rule validation and structured execution details, no unrealistic claims, ultra detailed 16:9",
        "negative_prompt": "",
        "pillar": "Risk controls",
        "archetype": "checklist",
    }
    monkeypatch.setattr(scheduler, "generate_content_package", lambda *_: candidate.copy())

    seen = {"caption": None}

    def fake_validate_caption(caption):
        seen["caption"] = caption
        return True, "ok"

    monkeypatch.setattr(scheduler, "validate_caption", fake_validate_caption)
    monkeypatch.setattr(scheduler, "validate_image_prompt", lambda *_: (True, "ok"))
    monkeypatch.setattr(scheduler, "generate_image", lambda *_: {"local_path": "images/generated/a.jpg", "remote_url": "https://replicate.delivery/x.jpg"})
    monkeypatch.setattr(scheduler, "upload_image", lambda *_: "https://local.host/images/generated/a.jpg")
    monkeypatch.setattr(scheduler, "post_to_meta", lambda *_: {"facebook": {"status": "skipped"}, "instagram": {"status": "skipped"}})

    scheduler.run_workflow(cfg, logger)
    assert seen["caption"] is not None
    lowered = seen["caption"].lower()
    for phrase in ["flawless execution", "smarter execution", "freeing you from emotional pitfalls"]:
        assert phrase not in lowered


def test_scheduler_replaces_malformed_gemini_caption_with_deterministic(monkeypatch):
    cfg = SimpleNamespace(max_generation_attempts=1, manual_review_mode=True, dry_run=True, prefer_local_public_image_url=False)
    logger = SimpleNamespace(info=lambda *a, **k: None, warning=lambda *a, **k: None, error=lambda *a, **k: None, exception=lambda *a, **k: None)
    candidate = {
        "caption": "Visit (Disclosure: XeanVI provides tools to help enforce user-defined rules. It does not Not financial advice. Trading involves risk.",
        "image_prompt": "p",
        "negative_prompt": "",
        "pillar": "Risk controls",
        "archetype": "checklist",
    }
    monkeypatch.setattr(scheduler, "generate_content_package", lambda *_: candidate.copy())
    seen = {"caption": None}

    def fake_validate_caption(caption):
        seen["caption"] = caption
        return True, "ok"

    monkeypatch.setattr(scheduler, "validate_caption", fake_validate_caption)
    monkeypatch.setattr(scheduler, "validate_image_prompt", lambda *_: (True, "ok"))
    monkeypatch.setattr(scheduler, "generate_image", lambda *_: {"local_path": "images/generated/a.jpg", "remote_url": "https://replicate.delivery/x.jpg"})
    monkeypatch.setattr(scheduler, "upload_image", lambda *_: "https://local.host/images/generated/a.jpg")
    monkeypatch.setattr(scheduler, "post_to_meta", lambda *_: {"facebook": {"status": "skipped"}, "instagram": {"status": "skipped"}})

    scheduler.run_workflow(cfg, logger)
    assert seen["caption"] is not None
    lowered = seen["caption"].lower()
    assert "visit" not in lowered
    assert "learn more at" not in lowered
    assert "disclosure:" not in lowered
