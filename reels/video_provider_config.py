from __future__ import annotations

import os
from dataclasses import dataclass
from pathlib import Path


@dataclass(frozen=True)
class ReelsVideoProviderConfig:
    provider: str = "manifest"
    renderer: str = "video"
    generate_video_clips: bool = True
    max_generated_clips_per_reel: int = 3
    comfyui_api_url: str = "http://127.0.0.1:8188"
    comfyui_workflow_path: Path = Path("workflows/reels_video_workflow.json")
    comfyui_prompt_node_id: str = ""
    comfyui_negative_prompt_node_id: str | None = None
    comfyui_seed_node_id: str | None = None
    comfyui_width: int = 720
    comfyui_height: int = 1280
    comfyui_frames: int = 81
    comfyui_fps: int = 24
    comfyui_timeout_seconds: int = 1800
    comfyui_poll_seconds: int = 5
    comfyui_model_family: str = "custom"


def _env_bool(name: str, default: bool) -> bool:
    v = os.getenv(name)
    if v is None:
        return default
    return v.strip().lower() in {"1", "true", "yes", "on"}


def load_video_provider_config() -> ReelsVideoProviderConfig:
    cfg = ReelsVideoProviderConfig(
        provider=os.getenv("REELS_VIDEO_PROVIDER", "manifest").strip().lower(),
        renderer=os.getenv("REELS_RENDERER", "video").strip().lower(),
        generate_video_clips=_env_bool("REELS_GENERATE_VIDEO_CLIPS", True),
        max_generated_clips_per_reel=int(os.getenv("REELS_MAX_GENERATED_CLIPS_PER_REEL", "3")),
        comfyui_api_url=os.getenv("COMFYUI_API_URL", "http://127.0.0.1:8188").strip(),
        comfyui_workflow_path=Path(os.getenv("COMFYUI_WORKFLOW_PATH", "workflows/reels_video_workflow.json").strip()),
        comfyui_prompt_node_id=os.getenv("COMFYUI_PROMPT_NODE_ID", "").strip(),
        comfyui_negative_prompt_node_id=(os.getenv("COMFYUI_NEGATIVE_PROMPT_NODE_ID", "").strip() or None),
        comfyui_seed_node_id=(os.getenv("COMFYUI_SEED_NODE_ID", "").strip() or None),
        comfyui_width=int(os.getenv("COMFYUI_WIDTH", "720")),
        comfyui_height=int(os.getenv("COMFYUI_HEIGHT", "1280")),
        comfyui_frames=int(os.getenv("COMFYUI_FRAMES", "81")),
        comfyui_fps=int(os.getenv("COMFYUI_FPS", "24")),
        comfyui_timeout_seconds=int(os.getenv("COMFYUI_TIMEOUT_SECONDS", "1800")),
        comfyui_poll_seconds=int(os.getenv("COMFYUI_POLL_SECONDS", "5")),
        comfyui_model_family=os.getenv("COMFYUI_MODEL_FAMILY", "custom").strip().lower(),
    )
    if cfg.provider not in {"comfy", "manifest", "none"}:
        raise ValueError("REELS_VIDEO_PROVIDER must be one of: comfy|manifest|none")
    if cfg.provider == "comfy":
        if not cfg.comfyui_prompt_node_id:
            raise ValueError("COMFYUI_PROMPT_NODE_ID is required when REELS_VIDEO_PROVIDER=comfy")
    return cfg
