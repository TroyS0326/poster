from __future__ import annotations

import argparse
from pathlib import Path

from reels.config import load_reel_config
from reels.tts import get_provider


def main() -> int:
    parser = argparse.ArgumentParser(description="Generate voiceover audio from reel storyboard JSON")
    parser.add_argument("--input", required=True, help="Path to reel config JSON")
    parser.add_argument("--output", required=True, help="Output audio path")
    parser.add_argument("--provider", default="silent", choices=["silent", "local_file", "edge_tts_optional"])
    parser.add_argument("--voice", default=None, help="Optional provider-specific voice name")
    parser.add_argument("--format", dest="audio_format", default=None, help="Optional output format (e.g. wav, mp3)")
    args = parser.parse_args()

    try:
        config = load_reel_config(args.input)
        provider = get_provider(args.provider)
        provider.generate(config=config, output=Path(args.output), voice=args.voice, audio_format=args.audio_format)
    except (FileNotFoundError, ValueError, RuntimeError) as exc:
        print(f"ERROR: {exc}")
        return 2

    print(f"Voiceover generated via provider={args.provider}: {Path(args.output).resolve()}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
