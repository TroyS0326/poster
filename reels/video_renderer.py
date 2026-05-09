from __future__ import annotations

from pathlib import Path

from moviepy import CompositeVideoClip, TextClip, VideoFileClip, concatenate_videoclips

from reels.config import ReelConfig
from reels.reel_templates import clamp_duration
from reels.video_assets import select_clip

EMPHASIS = {"rules", "risk", "stop", "emotion", "revenge", "overtrading", "discipline", "validation", "execution", "playbook", "automation"}


def _fit_vertical(clip: VideoFileClip, width: int, height: int) -> VideoFileClip:
    target = width / height
    ar = clip.w / clip.h
    if ar > target:
        nh = height
        nw = int(height * ar)
    else:
        nw = width
        nh = int(width / ar)
    clip = clip.resized(new_size=(nw, nh))
    x1 = max(0, (nw - width) // 2)
    y1 = max(0, (nh - height) // 2)
    return clip.cropped(x1=x1, y1=y1, x2=x1 + width, y2=y1 + height)


def render_video_reel(config: ReelConfig, output_path: str | Path, clips, template_name: str = "discipline_engine") -> None:
    out = Path(output_path)
    out.parent.mkdir(parents=True, exist_ok=True)
    duration = clamp_duration(config.duration_seconds)
    width, height = config.size
    scene_clips = []
    t_cursor = 0.0
    for i, sc in enumerate(config.scenes):
        tone = "cta" if i == len(config.scenes) - 1 else ("mistake" if any(x in sc.text.lower() for x in ["risk", "revenge", "overtrading", "mistake"]) else "discipline")
        asset = select_clip(clips, topic=config.title, scene_text=sc.text, template=template_name, tone=tone)
        base = VideoFileClip(asset.path, audio=False)
        seg_dur = min(max(1.2, sc.duration), 3.5)
        segment = _fit_vertical(base.subclipped(0, min(base.duration, seg_dur)), width, height)
        zoom = 1.08 if tone == "mistake" else 1.04
        segment = segment.resized(lambda t: 1.0 + (zoom - 1.0) * min(1.0, t / max(0.1, seg_dur)))

        words = sc.text.split()
        reveal = "\n".join(words[: min(len(words), 8)])
        txt = TextClip(text=reveal.upper(), font_size=72, color="white", stroke_color="black", stroke_width=3, method="caption", size=(int(width * 0.82), None))
        txt = txt.with_start(0).with_duration(seg_dur).with_position(("center", int(height * 0.72)))
        overlay_color = "#ff3b3b" if any(w.strip(',.!?').lower() in EMPHASIS and w.lower() in {"risk", "stop", "revenge", "overtrading", "emotion"} for w in words) else "#22d3ee"
        bar = TextClip(text="█", font_size=130, color=overlay_color).with_duration(seg_dur).with_position((50, 40))
        scene_clips.append(CompositeVideoClip([segment, txt, bar], size=(width, height)).with_duration(seg_dur))
        t_cursor += seg_dur
        if t_cursor >= duration:
            break
    final = concatenate_videoclips(scene_clips, method="compose").subclipped(0, min(duration, sum(c.duration for c in scene_clips)))
    final.write_videofile(str(out), codec="libx264", audio=False, fps=config.fps)
