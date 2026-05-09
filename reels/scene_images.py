from __future__ import annotations

import logging
import os
from pathlib import Path
from typing import Any

from PIL import Image

from image_ai import generate_image

LOGGER = logging.getLogger(__name__)

STYLE_MAP = {
    "premium_editorial_trading": "premium editorial finance photography, cinematic trading workstation, dramatic but professional",
    "cinematic_trading": "cinematic modern trading desk, realistic lighting, subtle depth",
}


def scene_prompt(topic: str, title: str, scene_text: str, style: str) -> str:
    style_text = STYLE_MAP.get(style, STYLE_MAP["premium_editorial_trading"])
    lower = scene_text.lower()
    tone = "tense and urgent" if any(k in lower for k in ["panic","revenge","overtrade","loss"]) else "calm, controlled, methodical"
    subject = "trader at multi-monitor desk" if "trader" in lower or "trade" in lower else "finance workstation with charts and checklist"
    return (
        f"Vertical 9:16 premium fintech editorial scene. Topic: {topic}. Title: {title}. Scene meaning: {scene_text}. "
        f"Emotional tone: {tone}. Subject/action: {subject}. "
        "Trading context with dashboards, risk-control motifs, terminal details, and cinematic depth. "
        "Composition: clear visual focal point plus protected text-safe area in left/center third for kinetic typography. "
        "Lighting/lens: moody low-key lighting, subtle bloom, shallow depth where useful, sharp details. "
        "No embedded text, no watermark, no logos, no social UI chrome. "
        f"Style direction: {style_text}."
    )


def _copy_or_convert(src: Path, dst: Path) -> Path:
    dst.parent.mkdir(parents=True, exist_ok=True)
    Image.open(src).convert("RGB").save(dst)
    return dst


def generate_scene_images(storyboard: dict[str, Any], item_dir: Path, *, style: str | None = None) -> list[str]:
    if not bool(str(os.getenv("REELS_GENERATE_SCENE_IMAGES", "true")).lower() in {"1", "true", "yes"}):
        return []

    topic = str(storyboard.get("topic", storyboard.get("title", "trading process")))
    title = str(storyboard.get("title", "Trading discipline"))
    scenes = storyboard.get("scenes") if isinstance(storyboard.get("scenes"), list) else []
    style_name = style or os.getenv("REELS_SCENE_IMAGE_STYLE", "premium_editorial_trading")

    class _Cfg:
        image_provider = os.getenv("REELS_SCENE_IMAGE_PROVIDER", "replicate")
        sd_api_url = os.getenv("SD_API_URL", "")
        sd_model = os.getenv("SD_MODEL", "")
        image_width = 1080
        image_height = 1920
        replicate_model = os.getenv("REPLICATE_MODEL", "")
        replicate_api_token = os.getenv("REPLICATE_API_TOKEN", "")
        replicate_output_format = "png"

    out_paths: list[str] = []
    fallback: Path | None = None
    for i, scene in enumerate(scenes, start=1):
        text = str(scene.get("text", "")) if isinstance(scene, dict) else ""
        prompt = scene_prompt(topic, title, text, style_name)
        result = generate_image(_Cfg, prompt, "no logos, no text, no watermark", LOGGER)
        out = item_dir / f"scene_{i:02d}.png"
        if result and result.get("local_path"):
            try:
                produced = _copy_or_convert(Path(result["local_path"]), out)
                fallback = produced
                out_paths.append(str(produced))
                continue
            except Exception:
                pass
        if fallback and fallback.exists():
            _copy_or_convert(fallback, out)
            out_paths.append(str(out))
    return out_paths
