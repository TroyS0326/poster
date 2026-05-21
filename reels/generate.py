from __future__ import annotations
import argparse, logging, os
from pathlib import Path
from reels.config import load_reel_config, ReelConfig  # re-exported for autopost

logger = logging.getLogger(__name__)

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
    if sc.image_path:
        p = Path(sc.image_path)
        if not p.is_absolute():
            p = Path(os.getcwd()) / p
        if p.exists():
            return Image.open(p).convert("RGB").resize((w, h), Image.LANCZOS)
    bg = config.background
    top = np.array(_hex_to_rgb(bg.color), dtype=np.float32)
    bot = np.array(_hex_to_rgb(bg.color_end), dtype=np.float32)
    blend = np.linspace(0, 1, h)[:, None]
    arr = (top * (1 - blend) + bot * blend).astype(np.uint8)
    return Image.fromarray(np.repeat(arr[:, None, :], w, axis=1), mode="RGB")

from reels.motion_styles import choose_motion

# ── keyword colour tables ─────────────────────────────────────────────────
DANGER_WORDS = {
    "broke","broken","loss","losses","losing","failed","fail","wrong",
    "mistake","cost","pain","hurt","fear","panic","revenge","emotional",
    "impulsive","overtraded","blown","ignored","melt","sinking","stomach",
    "losing","blew","blowup","bad","worst","never","always","stop",
}
ACCENT_WORDS = {
    "rules","rule","system","discipline","process","plan","consistent",
    "consistency","control","validated","playbook","xeanvi","accountability",
    "structure","execution","trust","rebuild","rebuilding","start","master",
    "winning","win","profit","growth","edge","clarity","confidence",
}

def _word_color(word, accent_rgb, danger_rgb, default_rgb):
    clean = word.lower().strip(".,!?\"'()")
    if clean in DANGER_WORDS: return danger_rgb
    if clean in ACCENT_WORDS: return accent_rgb
    return default_rgb

def _draw_text_shadow(draw, pos, text, font, fill, shadow_color=(0,0,0), layers=3):
    """Multi-layer shadow for strong text pop."""
    x, y = pos
    for i in range(layers, 0, -1):
        alpha = int(fill[3] * 0.5) if len(fill) > 3 else 200
        draw.text((x+i*2, y+i*2), text, font=font, fill=(*shadow_color, alpha))
    draw.text(pos, text, font=font, fill=fill)

def _draw_pill(draw, x, y, w, h, fill, outline=None, radius=24, outline_width=3):
    draw.rounded_rectangle([x, y, x+w, y+h], radius=radius, fill=fill)
    if outline:
        draw.rounded_rectangle([x, y, x+w, y+h], radius=radius,
                               outline=outline, width=outline_width)

def render_reel(config, output_path) -> None:
    import numpy as np
    from PIL import Image, ImageDraw, ImageFilter
    from moviepy import AudioFileClip, VideoClip
    from reels.config import load_reel_config
    from reels.typography import load_font

    out = Path(output_path)
    out.parent.mkdir(parents=True, exist_ok=True)
    w, h = config.size

    # ── palette ──────────────────────────────────────────────────────────
    ACCENT   = (0,   212, 255)   # electric cyan
    ACCENT2  = (100, 255, 200)   # mint green
    DANGER   = (255,  70,  80)   # hot red
    WHITE    = (255, 255, 255)
    DARK     = (  4,   7,  16)
    GOLD     = (255, 210,  80)   # CTA gold

    # ── fonts ─────────────────────────────────────────────────────────────
    hook_sz  = max(72, int(h * 0.075))
    body_sz  = max(52, int(h * 0.052))
    label_sz = max(32, int(h * 0.030))
    micro_sz = max(26, int(h * 0.024))

    hook_font  = load_font(hook_sz,  bold=True)
    body_font  = load_font(body_sz,  bold=True)
    label_font = load_font(label_sz, bold=True)
    micro_font = load_font(micro_sz, bold=False)

    scene_bgs = [_load_bg(config, i, w, h) for i in range(len(config.scenes))]

    # ── audio & duration sync ─────────────────────────────────────────────
    audio_clip = None
    render_duration = config.duration_seconds
    time_scale = 1.0

    if config.voiceover.enabled and config.voiceover.audio_path:
        ap = Path(config.voiceover.audio_path)
        if not ap.is_absolute():
            ap = Path(os.getcwd()) / ap
        if ap.exists():
            audio_clip = AudioFileClip(str(ap))
            render_duration = audio_clip.duration
            time_scale = render_duration / max(config.duration_seconds, 0.001)
            logger.info("Audio loaded: %.1fs from %s", render_duration, ap)
        else:
            logger.warning("Audio file not found: %s", ap)

    def make_frame(t):
        idx, scene, t0 = _scene_for_time(config, t, scale=time_scale)
        seg_dur = scene.duration * time_scale
        prog    = min(1.0, max(0.0, (t - t0) / max(seg_dur, 0.001)))
        is_hook = (idx == 0)
        is_cta  = (idx == len(config.scenes) - 1)

        # ── background + Ken Burns ────────────────────────────────────────
        base = scene_bgs[idx].copy()
        motion = choose_motion(scene.text)
        zoom   = motion.zoom_start + (motion.zoom_end - motion.zoom_start) * prog
        zw, zh = int(w / zoom), int(h / zoom)
        ox, oy = max(0, (w-zw)//2), max(0, (h-zh)//2)
        base   = base.crop((ox, oy, ox+zw, oy+zh)).resize((w, h), Image.LANCZOS)

        # ── dark overlay (heavier at bottom for text legibility) ──────────
        arr  = np.array(base, dtype=np.float32)
        dark = np.array(DARK,  dtype=np.float32)

        if is_hook:
            fade = min(1.0, t / 0.4)
            arr  = arr * (1 - 0.82*fade) + dark * (0.82*fade)
        else:
            # gradient: transparent at top → very dark at bottom
            split = int(h * 0.38)
            for row in range(h - split):
                a = (row / (h - split)) ** 0.45 * 0.92
                arr[split + row] = arr[split + row] * (1-a) + dark * a
            # also darken top strip for brand legibility
            for row in range(int(h*0.12)):
                a = (1 - row / (h*0.12)) * 0.70
                arr[row] = arr[row] * (1-a) + dark * a

        base = Image.fromarray(arr.clip(0,255).astype(np.uint8), "RGB")
        draw = ImageDraw.Draw(base, "RGBA")

        # ── progress bar ──────────────────────────────────────────────────
        bar_h = 6
        bar_w = int(w * min(1.0, t / render_duration))
        draw.rectangle([0, 0, w, bar_h], fill=(*DARK, 180))
        if bar_w > 0:
            # gradient bar: cyan → mint
            for i in range(bar_w):
                r = int(ACCENT[0] + (ACCENT2[0]-ACCENT[0]) * i/max(bar_w,1))
                g = int(ACCENT[1] + (ACCENT2[1]-ACCENT[1]) * i/max(bar_w,1))
                b = int(ACCENT[2] + (ACCENT2[2]-ACCENT[2]) * i/max(bar_w,1))
                draw.line([(i, 0), (i, bar_h)], fill=(r, g, b, 255))

        # ── brand label ───────────────────────────────────────────────────
        brand_y = int(h*0.022)
        draw.text((int(w*0.06), brand_y+2), "XEANVI",
                  font=label_font, fill=(0,0,0,160))
        draw.text((int(w*0.06), brand_y), "XEANVI",
                  font=label_font, fill=(*ACCENT, 230))

        # ── scene dots ────────────────────────────────────────────────────
        dot_x = int(w*0.78)
        dot_y = int(h*0.034)
        for di in range(len(config.scenes)):
            cx = dot_x + di * int(w*0.028)
            if di == idx:
                draw.ellipse([cx-7, dot_y-7, cx+7, dot_y+7],
                             fill=(*ACCENT2, 235))
            else:
                draw.ellipse([cx-4, dot_y-4, cx+4, dot_y+4],
                             fill=(80, 120, 150, 130))

        # ── text fade-in per scene ────────────────────────────────────────
        scene_prog = min(1.0, (t - t0) / 0.25)
        text_alpha = int(255 * scene_prog)

        # ─────────────────────────────────────────────────────────────────
        # HOOK scene — big dramatic top-center text
        # ─────────────────────────────────────────────────────────────────
        if is_hook:
            txt   = _short(scene.text, n=8)
            lines = _wrap(draw, txt, hook_font, int(w * 0.84))[:3]
            lh    = hook_font.size + 22
            total = len(lines) * lh
            ty    = int(h * 0.32) - total // 2

            for line in lines:
                words = line.split()
                lw    = sum(draw.textbbox((0,0), wd+" ", font=hook_font)[2] for wd in words)
                tx    = (w - lw) // 2
                for wd in words:
                    col = _word_color(wd, ACCENT2, DANGER, WHITE)
                    sw  = draw.textbbox((0,0), wd+" ", font=hook_font)[2]
                    # thick shadow
                    for ox2, oy2 in [(4,4),(3,3),(2,2)]:
                        draw.text((tx+ox2, ty+oy2), wd+" ", font=hook_font,
                                  fill=(0,0,0,int(text_alpha*0.7)))
                    # main word
                    draw.text((tx, ty), wd+" ", font=hook_font,
                              fill=(*col, text_alpha))
                    tx += sw
                ty += lh

            # subtle divider line under hook text
            if scene_prog > 0.6:
                line_alpha = int(text_alpha * 0.6)
                lx = int(w*0.15)
                draw.line([(lx, ty+8), (w-lx, ty+8)],
                          fill=(*ACCENT, line_alpha), width=2)

        # ─────────────────────────────────────────────────────────────────
        # MIDDLE scenes — frosted pill card, bottom third
        # ─────────────────────────────────────────────────────────────────
        elif not is_cta:
            txt   = _short(scene.text, n=11)
            lines = _wrap(draw, txt, body_font, int(w * 0.82))[:2]
            pad_x, pad_y = 36, 24
            lh    = body_font.size + 16
            total = len(lines) * lh
            pill_w = int(w * 0.90)
            pill_h = total + pad_y*2
            pill_x = (w - pill_w) // 2
            pill_y = int(h * 0.68)

            # pill bg — dark frosted glass
            _draw_pill(draw, pill_x, pill_y, pill_w, pill_h,
                       fill=(6, 10, 24, int(text_alpha*0.82)),
                       outline=(*ACCENT, int(text_alpha*0.55)),
                       radius=28, outline_width=2)

            # left accent bar
            bar_x = pill_x + 8
            draw.rounded_rectangle(
                [bar_x, pill_y+12, bar_x+4, pill_y+pill_h-12],
                radius=2, fill=(*ACCENT2, int(text_alpha*0.9)))

            ty = pill_y + pad_y
            for line in lines:
                tx = pill_x + pad_x + 16
                for wd in line.split():
                    col = _word_color(wd, ACCENT2, DANGER, WHITE)
                    sw  = draw.textbbox((0,0), wd+" ", font=body_font)[2]
                    draw.text((tx+2, ty+2), wd+" ", font=body_font,
                              fill=(0,0,0,int(text_alpha*0.6)))
                    draw.text((tx, ty), wd+" ", font=body_font,
                              fill=(*col, text_alpha))
                    tx += sw
                ty += lh

        # ─────────────────────────────────────────────────────────────────
        # CTA scene — gold button design
        # ─────────────────────────────────────────────────────────────────
        else:
            txt   = _short(scene.text, n=12)
            lines = _wrap(draw, txt, body_font, int(w * 0.80))[:2]
            pad_x, pad_y = 36, 28
            lh    = body_font.size + 16
            total = len(lines) * lh
            pill_w = int(w * 0.90)
            pill_h = total + pad_y*2
            pill_x = (w - pill_w) // 2
            pill_y = int(h * 0.65)

            # gold-bordered CTA card
            _draw_pill(draw, pill_x, pill_y, pill_w, pill_h,
                       fill=(12, 18, 38, int(text_alpha*0.90)),
                       outline=(*GOLD, int(text_alpha*0.85)),
                       radius=28, outline_width=3)

            ty = pill_y + pad_y
            for line in lines:
                tx = pill_x + pad_x
                for wd in line.split():
                    col = _word_color(wd, GOLD, DANGER, WHITE)
                    sw  = draw.textbbox((0,0), wd+" ", font=body_font)[2]
                    draw.text((tx+2, ty+2), wd+" ", font=body_font,
                              fill=(0,0,0,int(text_alpha*0.65)))
                    draw.text((tx, ty), wd+" ", font=body_font,
                              fill=(*col, text_alpha))
                    tx += sw
                ty += lh

            # "LEARN MORE →" micro badge
            badge_y = pill_y + pill_h + 16
            badge_txt = "LEARN MORE  →"
            bw = draw.textbbox((0,0), badge_txt, font=micro_font)[2]
            bx = (w - bw) // 2
            draw.text((bx, badge_y), badge_txt, font=micro_font,
                      fill=(*GOLD, int(text_alpha*0.9)))

        return np.array(base)

    clip = VideoClip(frame_function=make_frame, duration=render_duration)
    if audio_clip:
        clip = clip.with_audio(audio_clip)

    clip.write_videofile(str(out), codec="libx264", audio_codec="aac",
                         fps=config.fps, logger=None,
                         ffmpeg_params=["-crf","18","-preset","fast","-movflags","+faststart"])

def main() -> int:
    from reels.config import load_reel_config
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
