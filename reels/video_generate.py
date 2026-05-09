from __future__ import annotations

import argparse

from reels.config import load_reel_config
from reels.video_assets import load_video_manifest
from reels.video_renderer import render_video_reel


def main() -> int:
    p = argparse.ArgumentParser()
    p.add_argument("--input", required=True)
    p.add_argument("--output", required=True)
    p.add_argument("--manifest", required=True)
    p.add_argument("--template", default="discipline_engine")
    a = p.parse_args()
    cfg = load_reel_config(a.input)
    clips = load_video_manifest(a.manifest)
    render_video_reel(cfg, a.output, clips=clips, template_name=a.template)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
