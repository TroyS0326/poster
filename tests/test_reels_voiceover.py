import json
import subprocess
import sys
import wave
from pathlib import Path

import pytest

from reels.storyboard import generate_storyboard
from reels.tts import get_provider


def test_placeholder_generator_creates_wav(tmp_path: Path) -> None:
    payload = generate_storyboard(topic="Why rules matter")
    input_path = tmp_path / "storyboard.json"
    output_wav = tmp_path / "audio" / "placeholder.wav"
    input_path.write_text(json.dumps(payload), encoding="utf-8")

    result = subprocess.run(
        [sys.executable, "-m", "reels.voiceover", "--input", str(input_path), "--output", str(output_wav)],
        check=False,
        capture_output=True,
        text=True,
    )
    assert result.returncode == 0, result.stdout + result.stderr
    assert output_wav.exists()


def test_placeholder_generator_duration_matches(tmp_path: Path) -> None:
    payload = generate_storyboard(topic="Why rules matter", duration_seconds=12)
    input_path = tmp_path / "storyboard.json"
    output_wav = tmp_path / "placeholder.wav"
    input_path.write_text(json.dumps(payload), encoding="utf-8")

    result = subprocess.run(
        [sys.executable, "-m", "reels.voiceover", "--input", str(input_path), "--output", str(output_wav)],
        check=False,
        capture_output=True,
        text=True,
    )
    assert result.returncode == 0, result.stdout + result.stderr

    with wave.open(str(output_wav), "rb") as wav_file:
        duration = wav_file.getnframes() / float(wav_file.getframerate())
    assert abs(duration - 12.0) < 0.2


def test_placeholder_generator_rejects_non_wav_output(tmp_path: Path) -> None:
    payload = generate_storyboard(topic="Why rules matter")
    input_path = tmp_path / "storyboard.json"
    input_path.write_text(json.dumps(payload), encoding="utf-8")

    result = subprocess.run(
        [
            sys.executable,
            "-m",
            "reels.voiceover",
            "--input",
            str(input_path),
            "--output",
            str(tmp_path / "bad.mp3"),
            "--provider",
            "silent",
        ],
        check=False,
        capture_output=True,
        text=True,
    )
    assert result.returncode != 0
    assert "requires output path ending in .wav" in (result.stdout + result.stderr)


def test_placeholder_generator_rejects_missing_input_json(tmp_path: Path) -> None:
    result = subprocess.run(
        [sys.executable, "-m", "reels.voiceover", "--input", str(tmp_path / "missing.json"), "--output", str(tmp_path / "out.wav")],
        check=False,
        capture_output=True,
        text=True,
    )
    assert result.returncode != 0
    assert "not found" in (result.stdout + result.stderr).lower()


def test_edge_provider_requires_script(tmp_path: Path) -> None:
    payload = generate_storyboard(topic="Why rules matter")
    payload["voiceover"] = {"enabled": True, "provider": "edge_tts_optional", "audio_path": str(tmp_path / "out.mp3")}
    input_path = tmp_path / "storyboard.json"
    input_path.write_text(json.dumps(payload), encoding="utf-8")

    result = subprocess.run(
        [sys.executable, "-m", "reels.voiceover", "--input", str(input_path), "--output", str(tmp_path / "out.mp3"), "--provider", "edge_tts_optional"],
        check=False,
        capture_output=True,
        text=True,
    )
    assert result.returncode != 0
    assert "voiceover.script is required" in (result.stdout + result.stderr)


def test_edge_provider_missing_dependency_fails_clearly(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> None:
    payload = generate_storyboard(topic="Why rules matter", include_voiceover_script=True)
    input_path = tmp_path / "storyboard.json"
    output = tmp_path / "out.mp3"
    input_path.write_text(json.dumps(payload), encoding="utf-8")

    import builtins

    orig_import = builtins.__import__

    def _fake_import(name, *args, **kwargs):
        if name == "edge_tts":
            raise ImportError("missing edge_tts")
        return orig_import(name, *args, **kwargs)

    monkeypatch.setattr(builtins, "__import__", _fake_import)

    provider = get_provider("edge_tts_optional")
    from reels.config import load_reel_config

    with pytest.raises(RuntimeError, match="requires optional dependency 'edge-tts'"):
        provider.generate(config=load_reel_config(input_path), output=output)


def test_compliance_banned_script_rejected(tmp_path: Path) -> None:
    payload = generate_storyboard(topic="Why rules matter")
    payload["voiceover"] = {"enabled": True, "provider": "edge_tts_optional", "script": "guaranteed profits from day one"}
    input_path = tmp_path / "storyboard.json"
    input_path.write_text(json.dumps(payload), encoding="utf-8")
    result = subprocess.run(
        [sys.executable, "-m", "reels.voiceover", "--input", str(input_path), "--output", str(tmp_path / "out.mp3"), "--provider", "edge_tts_optional"],
        check=False,
        capture_output=True,
        text=True,
    )
    assert result.returncode != 0
    assert "compliance" in (result.stdout + result.stderr).lower()
