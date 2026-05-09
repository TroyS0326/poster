from __future__ import annotations

import argparse
import os
from pathlib import Path

from reels.config import ReelConfig, load_reel_config


def _hex_to_rgb(hex_color: str) -> tuple[int, int, int]:
    color = hex_color.strip().lstrip("#")
    if len(color) != 6:
        return (17, 17, 17)
    return tuple(int(color[i : i + 2], 16) for i in (0, 2, 4))


def _make_gradient_frame(size: tuple[int, int], top: str, bottom: str):
    import numpy as np
    from PIL import Image
    w, h = size
    top_rgb = np.array(_hex_to_rgb(top), dtype=np.float32)
    bottom_rgb = np.array(_hex_to_rgb(bottom), dtype=np.float32)
    blend = np.linspace(0.0, 1.0, h, dtype=np.float32)[:, None]
    arr = (top_rgb * (1.0 - blend) + bottom_rgb * blend).astype(np.uint8)
    frame = np.repeat(arr[:, None, :], w, axis=1)
    return Image.fromarray(frame, mode="RGB")


def _load_background(config: ReelConfig):
    from PIL import Image
    size = config.size
    bg = config.background
    if bg.type == "gradient":
        return _make_gradient_frame(size, bg.color, bg.color_end)

    if bg.type in {"image", "video"} and bg.path:
        p = Path(bg.path)
        if p.exists() and p.suffix.lower() != ".mp4":
            return Image.open(p).convert("RGB").resize(size)

    return Image.new("RGB", size, _hex_to_rgb(bg.color))


def _wrap_text(draw, text: str, font, max_width: int) -> list[str]:
    words = text.split()
    lines: list[str] = []
    current = ""
    for word in words:
        candidate = f"{current} {word}".strip()
        box = draw.textbbox((0, 0), candidate, font=font)
        if box[2] <= max_width or not current:
            current = candidate
        else:
            lines.append(current)
            current = word
    if current:
        lines.append(current)
    return lines


def render_reel(config: ReelConfig, output_path: str | Path) -> None:
    try:
        import numpy as np
        from PIL import ImageDraw, ImageFont
        from moviepy import AudioFileClip, ImageSequenceClip
    except ImportError as exc:
        raise RuntimeError("moviepy is required. Install dependencies from requirements.txt") from exc

    out = Path(output_path)
    out.parent.mkdir(parents=True, exist_ok=True)

    w, h = config.size
    font_title = ImageFont.load_default()
    font_body = ImageFont.load_default()
    base_bg = _load_background(config)

    frames: list[np.ndarray] = []
    for scene in config.scenes:
        total_frames = max(1, int(scene.duration * config.fps))
        for i in range(total_frames):
            progress = i / total_frames
            frame = base_bg.copy()
            if config.background.type == "image":
                zoom = 1.0 + 0.04 * progress
                zw, zh = int(w / zoom), int(h / zoom)
                ox, oy = (w - zw) // 2, (h - zh) // 2
                frame = frame.crop((ox, oy, ox + zw, oy + zh)).resize((w, h))

            draw = ImageDraw.Draw(frame)
            title_lines = _wrap_text(draw, config.title, font_title, int(w * 0.85))
            scene_lines = _wrap_text(draw, scene.text, font_body, int(w * 0.85))

            y = int(h * 0.12)
            for line in title_lines:
                draw.text((int(w * 0.08), y), line, fill=(255, 255, 255), font=font_title)
                y += 30

            y = int(h * 0.60)
            fade = min(1.0, progress / 0.2, (1.0 - progress) / 0.2)
            text_color = tuple(int(255 * max(0.25, fade)) for _ in range(3))
            for line in scene_lines:
                draw.text((int(w * 0.08), y), line, fill=text_color, font=font_body)
                y += 28

            frames.append(np.array(frame))

    clip = ImageSequenceClip(frames, fps=config.fps)

    # Optional voiceover: supported via env/config path, otherwise silent video.
    if config.voiceover.enabled and config.voiceover.audio_path:
        audio_path = Path(config.voiceover.audio_path)
        if audio_path.exists():
            clip = clip.with_audio(AudioFileClip(str(audio_path)))

    clip = clip.with_duration(config.duration_seconds)
    clip.write_videofile(str(out), codec="libx264", audio_codec="aac", fps=config.fps)


def main() -> int:
    parser = argparse.ArgumentParser(description="Generate vertical MP4 reels from JSON config")
    parser.add_argument("--input", required=True, help="Path to reel config JSON")
    parser.add_argument("--output", required=True, help="Output MP4 path")
    args = parser.parse_args()

    try:
        config = load_reel_config(args.input)
        render_reel(config, args.output)
    except FileNotFoundError as exc:
        print(f"ERROR: {exc}")
        return 1
    except ValueError as exc:
        print(f"ERROR: {exc}")
        return 2
    except RuntimeError as exc:
        print(f"ERROR: {exc}")
        return 3
    except OSError as exc:
        print(f"ERROR: Failed to render reel: {exc}")
        return 4

    print(f"Reel generated: {os.path.abspath(args.output)}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
