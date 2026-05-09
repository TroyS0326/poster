from pathlib import Path

import pytest

from reels.publish_urls import build_public_output_url


def test_build_public_output_url_success(tmp_path, monkeypatch):
    monkeypatch.chdir(tmp_path)
    outputs_file = tmp_path / "outputs/queue/day_03/example/example.mp4"
    outputs_file.parent.mkdir(parents=True)
    outputs_file.write_bytes(b"ok")

    result = build_public_output_url(
        "https://example.trycloudflare.com",
        "outputs/queue/day_03/example/example.mp4",
    )
    assert result == "https://example.trycloudflare.com/reels/outputs/queue/day_03/example/example.mp4"


def test_build_public_output_url_rejects_outside_outputs(tmp_path, monkeypatch):
    monkeypatch.chdir(tmp_path)
    bad_file = tmp_path / "video.mp4"
    bad_file.write_bytes(b"x")

    with pytest.raises(ValueError, match="under outputs"):
        build_public_output_url("https://example.trycloudflare.com", bad_file)


def test_build_public_output_url_rejects_unsupported_extension(tmp_path, monkeypatch):
    monkeypatch.chdir(tmp_path)
    bad_file = tmp_path / "outputs/queue/day_03/example/example.txt"
    bad_file.parent.mkdir(parents=True)
    bad_file.write_text("x", encoding="utf-8")

    with pytest.raises(ValueError, match="unsupported"):
        build_public_output_url("https://example.trycloudflare.com", bad_file)
