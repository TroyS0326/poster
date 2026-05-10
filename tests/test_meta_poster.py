from types import SimpleNamespace

import meta_poster


class _Logger:
    def __init__(self):
        self.warnings = []

    def info(self, *args, **kwargs):
        return None

    def warning(self, msg, *args, **kwargs):
        if args:
            msg = msg % args
        self.warnings.append(msg)


class _Resp:
    def __init__(self, ok=True, payload=None, status_code=200):
        self.ok = ok
        self._payload = payload if payload is not None else {}
        self.status_code = status_code
        self.text = str(self._payload)

    def json(self):
        return self._payload


def _cfg(**overrides):
    base = dict(
        dry_run=False,
        post_to_facebook=True,
        post_to_instagram=True,
        meta_access_token="meta",
        meta_graph_version="v20.0",
        fb_page_id="fb123",
        ig_business_id="ig123",
    )
    base.update(overrides)
    return SimpleNamespace(**base)


def test_post_to_meta_default_attempts_both(monkeypatch):
    calls = []

    def fake_post(url, data, timeout):
        calls.append((url, data))
        if url.endswith("/media"):
            return _Resp(payload={"id": "creation_1"})
        if url.endswith("/media_publish"):
            return _Resp(payload={"id": "publish_1"})
        return _Resp(payload={"id": "fb_1"})

    monkeypatch.setattr(meta_poster.requests, "post", fake_post)
    monkeypatch.setattr(meta_poster, "_wait_for_ig_container_ready", lambda *_: {"ready": True, "response": {"status_code": "FINISHED"}})

    result = meta_poster.post_to_meta("caption", "https://img", _cfg(), _Logger())

    assert result["facebook"]["status"] == "success"
    assert result["instagram"]["status"] == "success"
    assert len(calls) == 3


def test_post_to_meta_skips_facebook_when_disabled(monkeypatch):
    calls = []

    def fake_post(url, data, timeout):
        calls.append(url)
        if url.endswith("/media"):
            return _Resp(payload={"id": "creation_1"})
        return _Resp(payload={"id": "publish_1"})

    monkeypatch.setattr(meta_poster.requests, "post", fake_post)
    monkeypatch.setattr(meta_poster, "_wait_for_ig_container_ready", lambda *_: {"ready": True, "response": {"status_code": "FINISHED"}})

    result = meta_poster.post_to_meta("caption", "https://img", _cfg(post_to_facebook=False), _Logger())

    assert result["facebook"] == {"status": "skipped", "reason": "disabled_by_config"}
    assert result["instagram"]["status"] == "success"
    assert all("/photos" not in call for call in calls)


def test_post_to_meta_skips_instagram_when_disabled(monkeypatch):
    calls = []

    def fake_post(url, data, timeout):
        calls.append(url)
        return _Resp(payload={"id": "fb_1"})

    monkeypatch.setattr(meta_poster.requests, "post", fake_post)

    result = meta_poster.post_to_meta("caption", "https://img", _cfg(post_to_instagram=False), _Logger())

    assert result["facebook"]["status"] == "success"
    assert result["instagram"] == {"status": "skipped", "reason": "disabled_by_config"}
    assert all("/media" not in call for call in calls)


def test_post_to_meta_skips_both_when_both_disabled(monkeypatch):
    calls = []
    logger = _Logger()

    monkeypatch.setattr(meta_poster.requests, "post", lambda *a, **k: calls.append(a) or _Resp(payload={"id": "x"}))

    result = meta_poster.post_to_meta("caption", "https://img", _cfg(post_to_facebook=False, post_to_instagram=False), logger)

    assert result["facebook"] == {"status": "skipped", "reason": "disabled_by_config"}
    assert result["instagram"] == {"status": "skipped", "reason": "disabled_by_config"}
    assert calls == []
    assert any("both Meta platforms are disabled" in msg for msg in logger.warnings)


def test_post_to_meta_dry_run_skips_both(monkeypatch):
    calls = []
    monkeypatch.setattr(meta_poster.requests, "post", lambda *a, **k: calls.append(a) or _Resp(payload={"id": "x"}))

    result = meta_poster.post_to_meta("caption", "https://img", _cfg(dry_run=True), _Logger())

    assert result["dry_run"] is True
    assert result["facebook"] == {"status": "skipped", "reason": "dry_run"}
    assert result["instagram"] == {"status": "skipped", "reason": "dry_run"}
    assert calls == []
