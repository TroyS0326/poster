from __future__ import annotations

import argparse
import os
from pathlib import Path

from reels.config import ReelConfig, load_reel_config


def _hex_to_rgb(hex_color: str) -> tuple[int, int, int]:
    color = hex_color.strip().lstrip("#")
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


def _load_font(height: int, size_ratio: float, bold: bool):
    from PIL import ImageFont

    target_size = max(18, int(height * size_ratio))
    font_candidates = [
        "/usr/share/fonts/truetype/dejavu/DejaVuSans-Bold.ttf" if bold else "/usr/share/fonts/truetype/dejavu/DejaVuSans.ttf",
        "/usr/share/fonts/truetype/dejavu/DejaVuSans.ttf",
    ]
    for font_path in font_candidates:
        if Path(font_path).exists():
            return ImageFont.truetype(font_path, target_size)
    return ImageFont.load_default()


def _load_background(config: ReelConfig):
    from PIL import Image

    size = config.size
    bg = config.background
    if bg.type == "gradient":
        return _make_gradient_frame(size, bg.color, bg.color_end)

    if bg.type == "image" and bg.path:
        p = Path(bg.path)
        if not p.exists():
            raise ValueError(f"background.path does not exist: {p}")
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


def _scene_for_time(config: ReelConfig, t: float):
    elapsed = 0.0
    for scene in config.scenes:
        elapsed += scene.duration
        if t < elapsed:
            return scene
    return config.scenes[-1]


def _scene_start_time(config: ReelConfig, target_scene) -> float:
    elapsed = 0.0
    for scene in config.scenes:
        if scene is target_scene:
            return elapsed
        elapsed += scene.duration
    return 0.0


def render_reel(config: ReelConfig, output_path: str | Path) -> None:
    try:
        import numpy as np
        from PIL import ImageDraw
        from moviepy import AudioFileClip, VideoClip
    except ImportError as exc:
        raise RuntimeError(
            "moviepy and ffmpeg are required. Install requirements and ensure ffmpeg is on PATH"
        ) from exc

    out = Path(output_path)
    out.parent.mkdir(parents=True, exist_ok=True)

    w, h = config.size
    margin = int(w * 0.08)
    text_width = w - (margin * 2)

    font_title = _load_font(h, 0.05, bold=True)
    font_body = _load_font(h, 0.042, bold=False)
    title_spacing = max(10, int(h * 0.012))
    body_spacing = max(10, int(h * 0.01))

    base_bg = _load_background(config)
    scene_bg = {}
    for i, sc in enumerate(config.scenes):
        if sc.image_path and Path(sc.image_path).exists():
            from PIL import Image
            scene_bg[i] = Image.open(sc.image_path).convert("RGB").resize((w, h))

    def make_frame(t: float):
        scene = _scene_for_time(config, t)
        frame = base_bg.copy()
        scene_idx = config.scenes.index(scene)
        if scene_idx in scene_bg:
            frame = scene_bg[scene_idx].copy()
        elif scene_bg:
            frame = next(iter(scene_bg.values())).copy()

        progress = (t - _scene_start_time(config, scene)) / max(scene.duration, 0.001)
        zoom = 1.0 + 0.07 * max(0.0, min(1.0, progress))
        zw, zh = int(w / zoom), int(h / zoom)
        ox, oy = (w - zw) // 2, (h - zh) // 2
        frame = frame.crop((ox, oy, ox + zw, oy + zh)).resize((w, h))

        draw = ImageDraw.Draw(frame, "RGBA")
        draw.rectangle((0, int(h*0.5), w, h), fill=(0,0,0,95))
        title_lines = _wrap_text(draw, config.title, font_title, text_width)
        scene_lines = _wrap_text(draw, scene.text, font_body, text_width)

        y = int(h * 0.12)
        for line in title_lines:
            draw.text(
                (margin, y),
                line,
                fill=(255, 255, 255),
                font=font_title,
                stroke_width=max(1, int(h * 0.0025)),
                stroke_fill=(0, 0, 0),
            )
            y += font_title.size + title_spacing

        y = int(h * 0.58)
        for line in scene_lines:
            draw.text(
                (margin, y),
                line,
                fill=(255, 255, 255),
                font=font_body,
                stroke_width=max(2, int(h * 0.0025)),
                stroke_fill=(0, 0, 0),
            )
            y += font_body.size + body_spacing

        return np.array(frame)

    clip = VideoClip(frame_function=make_frame, duration=config.duration_seconds)

    if config.voiceover.enabled and config.voiceover.audio_path:
        audio_path = Path(config.voiceover.audio_path)
        if audio_path.exists():
            clip = clip.with_audio(AudioFileClip(str(audio_path)))

    try:
        clip.write_videofile(str(out), codec="libx264", audio_codec="aac", fps=config.fps)
    except OSError as exc:
        raise RuntimeError(
            "Failed to render video. Ensure ffmpeg is installed and accessible on PATH"
        ) from exc


def main() -> int:
    parser = argparse.ArgumentParser(description="Generate vertical MP4 reels from JSON config")
    parser.add_argument("--input", required=True, help="Path to reel config JSON")
    parser.add_argument("--output", required=True, help="Output MP4 path")
    args = parser.parse_args()

    try:
        config = load_reel_config(args.input)
        render_reel(config, args.output)
    except (FileNotFoundError, ValueError) as exc:
        print(f"ERROR: {exc}")
        return 2
    except RuntimeError as exc:
        print(f"ERROR: {exc}")
        return 3

    print(f"Reel generated: {os.path.abspath(args.output)}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
