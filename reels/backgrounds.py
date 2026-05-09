from __future__ import annotations

import argparse
from pathlib import Path

import numpy as np
from PIL import Image

from reels.visuals import resolve_visual_style


STYLE_RGB = {
    "fintech_dark": ((11, 18, 32), (30, 41, 59)),
    "workstation": ((31, 41, 55), (55, 65, 81)),
    "abstract_risk": ((20, 33, 61), (34, 58, 94)),
    "market_grid": ((15, 23, 42), (19, 78, 74)),
    "minimal_gradient": ((16, 24, 32), (31, 64, 104)),
}


def generate_background_png(style: str, brand: str, output: Path, size: tuple[int, int] = (1080, 1920)) -> Path:
    if output.suffix.lower() != ".png":
        raise ValueError("output path must end with .png")

    resolved_style = resolve_visual_style(brand=brand, visual_style=style)
    start, end = STYLE_RGB[resolved_style]

    width, height = size
    y = np.linspace(0.0, 1.0, height).reshape(height, 1, 1)
    start_arr = np.array(start, dtype=np.float32).reshape(1, 1, 3)
    end_arr = np.array(end, dtype=np.float32).reshape(1, 1, 3)
    gradient = (start_arr * (1.0 - y) + end_arr * y).astype(np.uint8)
    img = np.repeat(gradient, width, axis=1)

    # subtle vertical grid accent for style identity
    if resolved_style in {"market_grid", "fintech_dark"}:
        img[:, ::60, :] = np.clip(img[:, ::60, :] + 12, 0, 255)

    output.parent.mkdir(parents=True, exist_ok=True)
    Image.fromarray(img, mode="RGB").save(output)
    return output


def main() -> int:
    parser = argparse.ArgumentParser(description="Generate local PNG background for reels styles")
    parser.add_argument("--style", required=True)
    parser.add_argument("--brand", default="generic")
    parser.add_argument("--output", required=True)
    args = parser.parse_args()

    try:
        out = generate_background_png(style=args.style, brand=args.brand, output=Path(args.output))
    except ValueError as exc:
        print(f"ERROR: {exc}")
        return 2

    print(f"Background PNG generated: {out.resolve()}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
