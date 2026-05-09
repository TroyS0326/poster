import json
from types import SimpleNamespace

import pytest

from reels import publish


def _cfg():
    return SimpleNamespace(
        public_base_url="",
        post_dry_run=False,
        post_to_instagram=True,
        post_to_facebook=True,
        cleanup_after_success=True,
        delete_after_success_extensions=(".mp4", ".wav", ".mp3", ".png"),
        meta_access_token="t",
        meta_graph_version="v20.0",
        fb_page_id="fb",
        ig_business_id="ig",
    )


def test_publish_dry_run_instagram_no_requests_post(tmp_path, monkeypatch):
    input_path = tmp_path / "outputs/queue/day_03/example/example.json"
    video_path = tmp_path / "outputs/queue/day_03/example/example.mp4"
    video_path.parent.mkdir(parents=True)
    input_path.write_text(json.dumps({"title": "Rule", "scenes": [{"text": "One rule"}]}), encoding="utf-8")
    video_path.write_bytes(b"mp4")
    monkeypatch.chdir(tmp_path)
    monkeypatch.setattr(publish, "load_publish_config", _cfg)
    monkeypatch.setattr(publish.requests, "post", lambda *a, **k: (_ for _ in ()).throw(AssertionError("no post")))

    result = publish.publish_reel(str(input_path), str(video_path), "instagram", True, "https://example.trycloudflare.com")
    assert result["instagram"]["status"] == "planned"


def test_publish_dry_run_facebook_no_requests_post(tmp_path, monkeypatch):
    input_path = tmp_path / "outputs/queue/day_03/example/example.json"
    video_path = tmp_path / "outputs/queue/day_03/example/example.mp4"
    video_path.parent.mkdir(parents=True)
    input_path.write_text("{}", encoding="utf-8")
    video_path.write_bytes(b"mp4")
    monkeypatch.chdir(tmp_path)
    monkeypatch.setattr(publish, "load_publish_config", _cfg)
    monkeypatch.setattr(publish.requests, "post", lambda *a, **k: (_ for _ in ()).throw(AssertionError("no post")))

    result = publish.publish_reel(str(input_path), str(video_path), "facebook", True, "https://example.trycloudflare.com")
    assert result["facebook"]["status"] == "planned"


def test_publish_combined_dry_run_returns_both(tmp_path, monkeypatch):
    input_path = tmp_path / "outputs/queue/day_03/example/example.json"
    video_path = tmp_path / "outputs/queue/day_03/example/example.mp4"
    video_path.parent.mkdir(parents=True)
    input_path.write_text("{}", encoding="utf-8")
    video_path.write_bytes(b"mp4")
    monkeypatch.chdir(tmp_path)
    monkeypatch.setattr(publish, "load_publish_config", _cfg)

    result = publish.publish_reel(str(input_path), str(video_path), "both", True, "https://example.trycloudflare.com")
    assert result["instagram"]["status"] == "planned"
    assert result["facebook"]["status"] == "planned"


def test_publish_fails_when_video_missing(tmp_path, monkeypatch):
    input_path = tmp_path / "outputs/queue/day_03/example/example.json"
    input_path.parent.mkdir(parents=True)
    input_path.write_text("{}", encoding="utf-8")
    monkeypatch.setattr(publish, "load_publish_config", _cfg)
    with pytest.raises(FileNotFoundError):
        publish.publish_reel(str(input_path), str(tmp_path / "missing.mp4"), "instagram", True, "https://example.trycloudflare.com")
