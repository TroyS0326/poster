import json
from types import SimpleNamespace

import pytest

from reels import publish


def test_publish_dry_run_outputs_url_and_no_meta_calls(tmp_path, monkeypatch, capsys):
    input_path = tmp_path / "outputs/queue/day_03/example/example.json"
    video_path = tmp_path / "outputs/queue/day_03/example/example.mp4"
    video_path.parent.mkdir(parents=True)
    input_path.write_text(json.dumps({"title": "Rule", "scenes": [{"texts": ["One rule"]}]}), encoding="utf-8")
    video_path.write_bytes(b"mp4")

    monkeypatch.chdir(tmp_path)
    monkeypatch.setattr(publish, "load_config", lambda: SimpleNamespace(meta_access_token="t", meta_graph_version="v20.0", ig_business_id="ig"))
    monkeypatch.setattr(publish, "load_publish_config", lambda: SimpleNamespace(public_base_url="", post_dry_run=True, post_to_instagram=True, post_to_facebook=False))

    def fail_post(*args, **kwargs):
        raise AssertionError("requests.post should not be called in dry run")

    monkeypatch.setattr(publish.requests, "post", fail_post)

    result = publish.publish_reel(
        input_path=str(input_path),
        video_path=str(video_path),
        platform="instagram",
        dry_run=True,
        public_base_url="https://example.trycloudflare.com",
    )
    out = capsys.readouterr().out
    assert result["video_url"] == "https://example.trycloudflare.com/reels/outputs/queue/day_03/example/example.mp4"
    assert "example.mp4" in out


def test_publish_fails_when_video_missing(tmp_path, monkeypatch):
    input_path = tmp_path / "outputs/queue/day_03/example/example.json"
    input_path.parent.mkdir(parents=True)
    input_path.write_text("{}", encoding="utf-8")

    monkeypatch.setattr(publish, "load_config", lambda: SimpleNamespace(meta_access_token="t", meta_graph_version="v20.0", ig_business_id="ig"))
    monkeypatch.setattr(publish, "load_publish_config", lambda: SimpleNamespace(public_base_url="", post_dry_run=True, post_to_instagram=True, post_to_facebook=False))

    with pytest.raises(FileNotFoundError, match="video file does not exist"):
        publish.publish_reel(
            input_path=str(input_path),
            video_path=str(tmp_path / "missing.mp4"),
            platform="instagram",
            dry_run=True,
            public_base_url="https://example.trycloudflare.com",
        )
