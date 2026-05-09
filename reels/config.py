from __future__ import annotations

import json
import re
from dataclasses import dataclass
from pathlib import Path
from typing import Any

HEX_COLOR_RE = re.compile(r"^#[0-9a-fA-F]{6}$")
ALLOWED_BACKGROUNDS = {"solid", "gradient", "image"}


@dataclass(frozen=True)
class BackgroundConfig:
    type: str = "solid"
    color: str = "#111111"
    color_end: str = "#222222"
    path: str | None = None


@dataclass(frozen=True)
class SceneConfig:
    text: str
    duration: float
    image_path: str | None = None


@dataclass(frozen=True)
class VoiceoverConfig:
    enabled: bool = False
    provider: str = ""
    audio_path: str = ""
    script: str = ""


@dataclass(frozen=True)
class ReelConfig:
    title: str
    duration_seconds: float
    size: tuple[int, int]
    fps: int
    background: BackgroundConfig
    scenes: list[SceneConfig]
    voiceover: VoiceoverConfig


def _require(data: dict[str, Any], key: str) -> Any:
    if key not in data:
        raise ValueError(f"Missing required field: {key}")
    return data[key]


def _validate_hex_color(value: str, field_name: str) -> str:
    if not isinstance(value, str) or not HEX_COLOR_RE.fullmatch(value.strip()):
        raise ValueError(f"{field_name} must be a valid #RRGGBB hex color")
    return value.strip()


def load_reel_config(path: str | Path) -> ReelConfig:
    path_obj = Path(path)
    if not path_obj.exists():
        raise FileNotFoundError(f"Input config file not found: {path_obj}")

    try:
        raw = json.loads(path_obj.read_text(encoding="utf-8"))
    except json.JSONDecodeError as exc:
        raise ValueError(f"Invalid JSON in {path_obj}: {exc}") from exc

    title = str(_require(raw, "title")).strip()
    if not title:
        raise ValueError("title must not be empty")

    try:
        duration_seconds = float(_require(raw, "duration_seconds"))
    except (TypeError, ValueError) as exc:
        raise ValueError("duration_seconds must be numeric and > 0") from exc
    if duration_seconds <= 0:
        raise ValueError("duration_seconds must be numeric and > 0")

    size_raw = raw.get("size", [1080, 1920])
    if not isinstance(size_raw, list) or len(size_raw) != 2:
        raise ValueError("size must be [width, height]")
    try:
        width, height = int(size_raw[0]), int(size_raw[1])
    except (TypeError, ValueError) as exc:
        raise ValueError("size must contain two positive integers") from exc
    if width <= 0 or height <= 0:
        raise ValueError("size must contain two positive integers")

    fps_raw = raw.get("fps", 24)
    try:
        fps = int(fps_raw)
    except (TypeError, ValueError) as exc:
        raise ValueError("fps must be numeric and > 0") from exc
    if fps <= 0:
        raise ValueError("fps must be numeric and > 0")

    bg_raw = raw.get("background", {})
    if not isinstance(bg_raw, dict):
        raise ValueError("background must be an object")

    bg_type = str(bg_raw.get("type", "solid")).strip().lower()
    if bg_type not in ALLOWED_BACKGROUNDS:
        raise ValueError("background.type must be one of: solid, gradient, image")

    color = _validate_hex_color(str(bg_raw.get("color", "#111111")), "background.color")
    color_end = _validate_hex_color(str(bg_raw.get("color_end", "#222222")), "background.color_end")

    bg_path_raw = bg_raw.get("path")
    bg_path = str(bg_path_raw).strip() if bg_path_raw is not None else None
    if bg_type == "image":
        if not bg_path:
            raise ValueError("background.path is required when background.type is 'image'")
        if not Path(bg_path).exists():
            raise ValueError(f"background.path does not exist: {bg_path}")

    background = BackgroundConfig(type=bg_type, color=color, color_end=color_end, path=bg_path)

    scenes_raw = _require(raw, "scenes")
    if not isinstance(scenes_raw, list) or not scenes_raw:
        raise ValueError("scenes must be a non-empty list")

    scenes: list[SceneConfig] = []
    total_scene_duration = 0.0
    for idx, scene in enumerate(scenes_raw):
        if not isinstance(scene, dict):
            raise ValueError(f"scene[{idx}] must be an object")

        text = str(scene.get("text", "")).strip()
        if not text:
            raise ValueError(f"scene[{idx}] text must not be empty")

        try:
            duration = float(scene.get("duration", 0))
        except (TypeError, ValueError) as exc:
            raise ValueError(f"scene[{idx}] duration must be numeric and > 0") from exc
        if duration <= 0:
            raise ValueError(f"scene[{idx}] duration must be numeric and > 0")

        image_path_raw = scene.get("image_path")
        image_path = str(image_path_raw).strip() if image_path_raw else None
        scenes.append(SceneConfig(text=text, duration=duration, image_path=image_path))
        total_scene_duration += duration

    if total_scene_duration > duration_seconds + 1e-9:
        raise ValueError("sum of scene durations cannot exceed duration_seconds")

    voice_raw = raw.get("voiceover", {})
    if not isinstance(voice_raw, dict):
        raise ValueError("voiceover must be an object")
    voiceover = VoiceoverConfig(
        enabled=bool(voice_raw.get("enabled", False)),
        provider=str(voice_raw.get("provider", "")),
        audio_path=str(voice_raw.get("audio_path", "")),
        script=str(voice_raw.get("script", "")).strip(),
    )

    return ReelConfig(
        title=title,
        duration_seconds=duration_seconds,
        size=(width, height),
        fps=fps,
        background=background,
        scenes=scenes,
        voiceover=voiceover,
    )
