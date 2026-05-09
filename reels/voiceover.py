from __future__ import annotations

import argparse
import wave
from pathlib import Path

from reels.config import load_reel_config


SAMPLE_RATE = 44100
CHANNELS = 1
SAMPLE_WIDTH_BYTES = 2


def write_silent_wav(output: Path, duration_seconds: float) -> None:
    if output.suffix.lower() != ".wav":
        raise ValueError("output path must end with .wav")
    if duration_seconds <= 0:
        raise ValueError("duration_seconds must be > 0")

    output.parent.mkdir(parents=True, exist_ok=True)
    frame_count = int(round(duration_seconds * SAMPLE_RATE))
    silence = b"\x00\x00" * frame_count

    with wave.open(str(output), "wb") as wav_file:
        wav_file.setnchannels(CHANNELS)
        wav_file.setsampwidth(SAMPLE_WIDTH_BYTES)
        wav_file.setframerate(SAMPLE_RATE)
        wav_file.writeframes(silence)


def main() -> int:
    parser = argparse.ArgumentParser(description="Generate silent placeholder WAV from reel storyboard JSON")
    parser.add_argument("--input", required=True, help="Path to reel config JSON")
    parser.add_argument("--output", required=True, help="Output WAV path")
    args = parser.parse_args()

    try:
        config = load_reel_config(args.input)
        write_silent_wav(Path(args.output), config.duration_seconds)
    except (FileNotFoundError, ValueError) as exc:
        print(f"ERROR: {exc}")
        return 2

    print(f"Placeholder silent WAV generated: {Path(args.output).resolve()}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
