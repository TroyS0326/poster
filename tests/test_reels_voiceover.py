import json
import subprocess
import sys
import wave
from pathlib import Path

from reels.storyboard import generate_storyboard


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
        [sys.executable, "-m", "reels.voiceover", "--input", str(input_path), "--output", str(tmp_path / "bad.mp3")],
        check=False,
        capture_output=True,
        text=True,
    )
    assert result.returncode != 0
    assert "must end with .wav" in (result.stdout + result.stderr)


def test_placeholder_generator_rejects_missing_input_json(tmp_path: Path) -> None:
    result = subprocess.run(
        [sys.executable, "-m", "reels.voiceover", "--input", str(tmp_path / "missing.json"), "--output", str(tmp_path / "out.wav")],
        check=False,
        capture_output=True,
        text=True,
    )
    assert result.returncode != 0
    assert "not found" in (result.stdout + result.stderr).lower()
