from __future__ import annotations
import argparse, os
from pathlib import Path
from reels.config import ReelConfig, load_reel_config
from reels.design_system import PALETTES
from reels.typography import load_font
from reels.motion_styles import choose_motion

def _hex_to_rgb(h):
    c = h.strip().lstrip("#")
    return tuple(int(c[i:i+2], 16) for i in (0, 2, 4))

def _scene_for_time(config, t, scale=1.0):
    elapsed = 0.0
    scaled_t = t / max(scale, 0.001)
    for i, scene in enumerate(config.scenes):
        elapsed += scene.duration
        if scaled_t < elapsed:
            return i, scene, (elapsed - scene.duration) * scale
    last = config.scenes[-1]
    return len(config.scenes)-1, last, max(0.0, config.duration_seconds - last.duration) * scale

def _wrap(draw, text, font, max_width):
    words = text.split()
    lines, cur = [], ""
    for word in words:
        cand = f"{cur} {word}".strip()
        if draw.textbbox((0,0), cand, font=font)[2] <= max_width or not cur:
            cur = cand
        else:
            lines.append(cur); cur = word
    if cur: lines.append(cur)
    return lines

def _short(text, n=9):
    words = text.split()
    if len(words) <= n: return text
    for i in range(n, min(len(words), n+4)):
        if words[i-1].endswith(('.', ',', '!', '?')): return ' '.join(words[:i])
    return ' '.join(words[:n])

def _load_bg(config, idx, w, h):
    from PIL import Image
    import numpy as np
    sc = config.scenes[idx]
    if sc.image_path and Path(sc.image_path).exists():
        return Image.open(sc.image_path).convert("RGB").resize((w, h), Image.LANCZOS)
    bg = config.background
    top = np.array(_hex_to_rgb(bg.color), dtype=np.float32)
    bot = np.array(_hex_to_rgb(bg.color_end), dtype=np.float32)
    blend = np.linspace(0, 1, h)[:, None]
    arr = (top * (1 - blend) + bot * blend).astype(np.uint8)
    return Image.fromarray(np.repeat(arr[:, None, :], w, axis=1), mode="RGB")

DANGER_WORDS = {"broke","broken","loss","losses","losing","failed","fail","wrong",
                "mistake","cost","pain","hurt","fear","panic","revenge","emotional",
                "impulsive","overtraded","blown","ignored","melt","sinking","stomach"}
ACCENT_WORDS = {"rules","rule","system","discipline","process","plan","consistent",
                "consistency","control","validated","playbook","xeanvi","accountability",
                "structure","execution","trust","rebuild","rebuilding","start"}

def _word_color(word, accent_rgb, danger_rgb, default_rgb):
    clean = word.lower().strip(".,!?\"'()")
    if clean in DANGER_WORDS: return danger_rgb
    if clean in ACCENT_WORDS: return accent_rgb
    return default_rgb

def _draw_pill(draw, x, y, w, h, color, radius=18):
    draw.rounded_rectangle([x, y, x+w, y+h], radius=radius, fill=color)

def render_reel(config: ReelConfig, output_path) -> None:
    import numpy as np
    from PIL import Image, ImageDraw
    from moviepy import AudioFileClip, VideoClip

    out = Path(output_path)
    out.parent.mkdir(parents=True, exist_ok=True)
    w, h = config.size
    palette = PALETTES["xeanvi_dark"]

    accent_rgb  = _hex_to_rgb(palette.accent)
    accent2_rgb = _hex_to_rgb(palette.accent_alt)
    danger_rgb  = _hex_to_rgb(palette.danger)
    text_rgb    = (238, 244, 255)
    dark_rgb    = (4, 7, 16)

    hook_font  = load_font(max(58, int(h * 0.068)), bold=True)
    body_font  = load_font(max(42, int(h * 0.048)), bold=True)
    label_font = load_font(max(28, int(h * 0.030)), bold=True)
    micro_font = load_font(max(24, int(h * 0.026)), bold=False)

    scene_bgs = [_load_bg(config, i, w, h) for i in range(len(config.scenes))]

    # Load audio and sync video duration to it
    audio_clip = None
    render_duration = config.duration_seconds
    time_scale = 1.0

    if (config.voiceover.enabled and config.voiceover.audio_path
            and Path(config.voiceover.audio_path).exists()):
        audio_clip = AudioFileClip(config.voiceover.audio_path)
        render_duration = audio_clip.duration
        time_scale = render_duration / max(config.duration_seconds, 0.001)

    def make_frame(t):
        idx, scene, t0 = _scene_for_time(config, t, scale=time_scale)
        seg_dur = scene.duration * time_scale
        prog = min(1.0, max(0.0, (t - t0) / max(seg_dur, 0.001)))
        is_hook = (idx == 0)
        is_cta  = (idx == len(config.scenes) - 1)

        base = scene_bgs[idx].copy()

        motion = choose_motion(scene.text)
        zoom = motion.zoom_start + (motion.zoom_end - motion.zoom_start) * prog
        zw, zh = int(w / zoom), int(h / zoom)
        ox, oy = max(0, (w - zw) // 2), max(0, (h - zh) // 2)
        base = base.crop((ox, oy, ox+zw, oy+zh)).resize((w, h), Image.LANCZOS)

        arr = np.array(base, dtype=np.float32)
        dark = np.array(dark_rgb, dtype=np.float32)

        if is_hook:
            fade = min(1.0, t / 0.35)
            arr = arr * (1 - 0.80 * fade) + dark * (0.80 * fade)
        else:
            ov_start = int(h * 0.45)
            for row in range(h - ov_start):
                a = (row / (h - ov_start)) ** 0.55 * 0.88
                arr[ov_start + row] = arr[ov_start + row] * (1 - a) + dark * a

        base = Image.fromarray(arr.clip(0, 255).astype(np.uint8), "RGB")
        draw = ImageDraw.Draw(base, "RGBA")

        # Progress bar
        bw = int(w * min(1.0, t / render_duration))
        draw.rectangle([0, 0, bw, 7], fill=(*accent2_rgb, 240))

        # Brand label
        draw.text((int(w*0.06), int(h*0.028)), "XEANVI",
                  font=label_font, fill=(*accent_rgb, 200))

        # Scene dots
        dot_x, dot_y = int(w * 0.82), int(h * 0.036)
        for di in range(len(config.scenes)):
            cx = dot_x + di * 22
            col = (*accent2_rgb, 230) if di == idx else (80, 100, 130, 140)
            r = 6 if di == idx else 4
            draw.ellipse([cx-r, dot_y-r, cx+r, dot_y+r], fill=col)

        text_alpha = int(255 * min(1.0, (t - t0) / 0.20))

        if is_hook:
            txt = _short(scene.text, n=8)
            lines = _wrap(draw, txt, hook_font, int(w * 0.82))[:2]
            total_h = len(lines) * (hook_font.size + 18)
            ty = int(h * 0.38) - total_h // 2
            for line in lines:
                words = line.split()
                full_w = sum(draw.textbbox((0,0), wd+" ", font=hook_font)[2] for wd in words)
                tx = (w - full_w) // 2
                for word in words:
                    col = _word_color(word, accent2_rgb, danger_rgb, (255,255,255))
                    sw = draw.textbbox((0,0), word+" ", font=hook_font)[2]
                    draw.text((tx+4, ty+4), word+" ", font=hook_font, fill=(0,0,0,int(text_alpha*0.6)))
                    draw.text((tx, ty), word+" ", font=hook_font, fill=(*col, text_alpha))
                    tx += sw
                ty += hook_font.size + 18

        elif is_cta:
            txt = _short(scene.text, n=11)
            lines = _wrap(draw, txt, body_font, int(w * 0.80))[:2]
            pad_x, pad_y = 32, 20
            line_h = body_font.size + 14
            total_h = len(lines) * line_h
            pill_w, pill_h = int(w * 0.86), total_h + pad_y * 2
            pill_x = (w - pill_w) // 2
            pill_y = int(h * 0.68)
            _draw_pill(draw, pill_x, pill_y, pill_w, pill_h,
                       (*accent2_rgb, int(text_alpha * 0.28)), radius=24)
            draw.rounded_rectangle([pill_x, pill_y, pill_x+pill_w, pill_y+pill_h],
                                   radius=24, outline=(*accent2_rgb, int(text_alpha*0.7)), width=3)
            ty = pill_y + pad_y
            for line in lines:
                tx = pill_x + pad_x
                for word in line.split():
                    col = _word_color(word, accent2_rgb, danger_rgb, (255,255,255))
                    sw = draw.textbbox((0,0), word+" ", font=body_font)[2]
                    draw.text((tx+2, ty+2), word+" ", font=body_font, fill=(0,0,0,int(text_alpha*0.5)))
                    draw.text((tx, ty), word+" ", font=body_font, fill=(*col, text_alpha))
                    tx += sw
                ty += line_h

        else:
            txt = _short(scene.text, n=10)
            lines = _wrap(draw, txt, body_font, int(w * 0.84))[:2]
            pad_x, pad_y = 28, 18
            line_h = body_font.size + 12
            total_h = len(lines) * line_h
            pill_w, pill_h = int(w * 0.88), total_h + pad_y * 2
            pill_x = (w - pill_w) // 2
            pill_y = int(h * 0.70)
            _draw_pill(draw, pill_x, pill_y, pill_w, pill_h,
                       (0, 0, 0, int(text_alpha * 0.55)), radius=20)
            ty = pill_y + pad_y
            for line in lines:
                tx = pill_x + pad_x
                for word in line.split():
                    col = _word_color(word, accent2_rgb, danger_rgb, text_rgb)
                    sw = draw.textbbox((0,0), word+" ", font=body_font)[2]
                    draw.text((tx+2, ty+2), word+" ", font=body_font, fill=(0,0,0,int(text_alpha*0.65)))
                    draw.text((tx, ty), word+" ", font=body_font, fill=(*col, text_alpha))
                    tx += sw
                ty += line_h

        return np.array(base)

    clip = VideoClip(frame_function=make_frame, duration=render_duration)
    if audio_clip:
        clip = clip.with_audio(audio_clip)
    clip.write_videofile(str(out), codec="libx264", audio_codec="aac",
                         fps=config.fps, logger=None)

def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--input", required=True)
    parser.add_argument("--output", required=True)
    args = parser.parse_args()
    try:
        config = load_reel_config(args.input)
        render_reel(config, args.output)
    except (FileNotFoundError, ValueError) as exc:
        print(f"ERROR: {exc}"); return 2
    except RuntimeError as exc:
        print(f"ERROR: {exc}"); return 3
    print(f"Reel generated: {os.path.abspath(args.output)}")
    return 0

if __name__ == "__main__":
    raise SystemExit(main())
