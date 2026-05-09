from __future__ import annotations

from pathlib import Path

from reels.video_prompts import build_scene_video_prompt
from reels.video_provider_comfy import generate_comfy_video_clip
from reels.video_provider_config import load_video_provider_config


def ensure_scene_video_clips(storyboard: dict, item_dir: Path, config=None) -> list[str]:
    cfg = config or load_video_provider_config()
    max_clips = max(1, int(cfg.max_generated_clips_per_reel))
    existing = []
    for i in range(1, max_clips + 1):
        p = item_dir / f"video_scene_{i:02d}.mp4"
        if p.exists():
            existing.append(str(p))
    if existing:
        return existing
    if cfg.provider == "manifest":
        return []
    if cfg.provider == "none":
        raise ValueError("REELS_VIDEO_PROVIDER=none cannot render REELS_RENDERER=video without clips")
    if not cfg.generate_video_clips:
        return []

    scenes = storyboard.get("scenes", []) if isinstance(storyboard, dict) else []
    if not scenes:
        raise ValueError("Storyboard has no scenes for video clip generation")
    selected = scenes[:max_clips]
    if len(scenes) > max_clips:
        selected[-1] = {"text": f"{selected[-1].get('text', '')}; {scenes[-1].get('text', '')}"}

    generated = []
    for idx, sc in enumerate(selected, start=1):
        prompt = build_scene_video_prompt(storyboard.get("title", "Trading scene"), sc.get("text", ""))
        out = item_dir / f"video_scene_{idx:02d}.mp4"
        generate_comfy_video_clip(
            prompt,
            out,
            api_url=cfg.comfyui_api_url,
            workflow_path=cfg.comfyui_workflow_path,
            prompt_node_id=cfg.comfyui_prompt_node_id,
            negative_prompt_node_id=cfg.comfyui_negative_prompt_node_id,
            seed_node_id=cfg.comfyui_seed_node_id,
            width=cfg.comfyui_width,
            height=cfg.comfyui_height,
            frames=cfg.comfyui_frames,
            fps=cfg.comfyui_fps,
            timeout_seconds=cfg.comfyui_timeout_seconds,
            poll_seconds=cfg.comfyui_poll_seconds,
        )
        generated.append(str(out))
    return generated
