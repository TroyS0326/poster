from __future__ import annotations

import argparse
import os
from pathlib import Path

from reels.config import ReelConfig, load_reel_config
from reels.design_system import PALETTES, choose_layout
from reels.motion_styles import choose_motion
from reels.typography import emphasis_color, load_font


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


def _load_background(config: ReelConfig):
    from PIL import Image

    bg = config.background
    if bg.type == "gradient":
        return _make_gradient_frame(config.size, bg.color, bg.color_end)
    if bg.type == "image" and bg.path:
        p = Path(bg.path)
        if p.exists():
            return Image.open(p).convert("RGB").resize(config.size)
    return Image.new("RGB", config.size, _hex_to_rgb(bg.color))


def _wrap_text(draw, text: str, font, max_width: int) -> list[str]:
    words = text.split()
    lines: list[str] = []
    current = ""
    for word in words:
        cand = f"{current} {word}".strip()
        if draw.textbbox((0, 0), cand, font=font)[2] <= max_width or not current:
            current = cand
        else:
            lines.append(current)
            current = word
    if current:
        lines.append(current)
    return lines


def _scene_for_time(config: ReelConfig, t: float):
    elapsed = 0.0
    for i, scene in enumerate(config.scenes):
        elapsed += scene.duration
        if t < elapsed:
            return i, scene, elapsed - scene.duration
    return len(config.scenes)-1, config.scenes[-1], max(0.0, config.duration_seconds - config.scenes[-1].duration)


def render_reel(config: ReelConfig, output_path: str | Path) -> None:
    import numpy as np
    from PIL import Image, ImageDraw
    from moviepy import AudioFileClip, VideoClip

    out = Path(output_path); out.parent.mkdir(parents=True, exist_ok=True)
    w, h = config.size
    palette = PALETTES["xeanvi_dark"]
    title_font = load_font(max(34, int(h * 0.05)), bold=True)
    body_font = load_font(max(28, int(h * 0.036)), bold=False)
    micro_font = load_font(max(20, int(h * 0.021)), bold=False)

    default_bg = _load_background(config)
    scene_bg: dict[int, Image.Image] = {}
    best_fallback = default_bg.copy()
    for i, sc in enumerate(config.scenes):
        if sc.image_path and Path(sc.image_path).exists():
            img = Image.open(sc.image_path).convert("RGB").resize((w, h))
            scene_bg[i] = img
            best_fallback = img

    def make_frame(t: float):
        idx, scene, start = _scene_for_time(config, t)
        progress = min(1.0, max(0.0, (t - start) / max(scene.duration, 0.001)))
        motion = choose_motion(scene.text)
        layout = choose_layout(idx, scene.text)
        base = scene_bg.get(idx, best_fallback).copy()

        # motion
        zoom = motion.zoom_start + (motion.zoom_end - motion.zoom_start) * progress
        zw, zh = int(w / zoom), int(h / zoom)
        ox = int((w - zw) * (0.5 + motion.pan_x * (progress - 0.5)))
        oy = int((h - zh) * (0.5 + motion.pan_y * (progress - 0.5)))
        base = base.crop((max(0, ox), max(0, oy), max(0, ox) + zw, max(0, oy) + zh)).resize((w, h))

        draw = ImageDraw.Draw(base, "RGBA")
        # premium overlays
        for y in range(0, h, 90):
            draw.line((0, y, w, y), fill=(60, 120, 180, 24), width=1)
        for x in range(0, w, 120):
            draw.line((x, 0, x, h), fill=(40, 170, 150, 18), width=1)
        draw.rectangle((0, int(h * 0.64), w, h), fill=(5, 8, 14, 155))
        draw.rectangle((int(w*0.06), int(h*0.08), int(w*0.94), int(h*0.14)), fill=(10, 26, 45, 110))
        draw.text((int(w*0.08), int(h*0.095)), "XEANVI // DISCIPLINE ENGINE", font=micro_font, fill=(140, 201, 255))

        # text animation: stagger line reveal
        title_lines = _wrap_text(draw, config.title, title_font, int(w * 0.84))
        scene_lines = _wrap_text(draw, scene.text, body_font, int(w * 0.84))
        show_title_lines = max(1, int(progress * len(title_lines) + 0.5))
        show_scene_lines = max(1, int(progress * len(scene_lines) + 0.2))

        tx = int(w * 0.08) if "left" in layout else int(w * 0.12)
        ty = int(h * 0.18)
        for ln in title_lines[:show_title_lines]:
            draw.text((tx, ty), ln, font=title_font, fill=palette.text)
            ty += title_font.size + 8
        sy = int(h * 0.68)
        for ln in scene_lines[:show_scene_lines]:
            cursor_x = tx
            for word in ln.split():
                color = emphasis_color(word, palette)
                draw.text((cursor_x, sy), word + " ", font=body_font, fill=color)
                cursor_x += draw.textbbox((0,0), word + " ", font=body_font)[2]
            sy += body_font.size + 6

        return np.array(base)

    clip = VideoClip(frame_function=make_frame, duration=config.duration_seconds)
    if config.voiceover.enabled and config.voiceover.audio_path and Path(config.voiceover.audio_path).exists():
        clip = clip.with_audio(AudioFileClip(config.voiceover.audio_path))
    clip.write_videofile(str(out), codec="libx264", audio_codec="aac", fps=config.fps)


def main() -> int:
    parser = argparse.ArgumentParser(description="Generate vertical MP4 reels from JSON config")
    parser.add_argument("--input", required=True)
    parser.add_argument("--output", required=True)
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
