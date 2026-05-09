from __future__ import annotations

import json
from dataclasses import dataclass
from pathlib import Path
from typing import Any


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


@dataclass(frozen=True)
class VoiceoverConfig:
    enabled: bool = False
    provider: str = ""
    audio_path: str = ""


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

    duration_seconds = float(_require(raw, "duration_seconds"))
    if duration_seconds <= 0:
        raise ValueError("duration_seconds must be > 0")

    size_raw = raw.get("size", [1080, 1920])
    if not isinstance(size_raw, list) or len(size_raw) != 2:
        raise ValueError("size must be [width, height]")
    width, height = int(size_raw[0]), int(size_raw[1])
    if width <= 0 or height <= 0:
        raise ValueError("size values must be > 0")

    fps = int(raw.get("fps", 24))
    if fps <= 0:
        raise ValueError("fps must be > 0")

    bg_raw = raw.get("background", {})
    background = BackgroundConfig(
        type=str(bg_raw.get("type", "solid")),
        color=str(bg_raw.get("color", "#111111")),
        color_end=str(bg_raw.get("color_end", "#222222")),
        path=bg_raw.get("path"),
    )

    scenes_raw = _require(raw, "scenes")
    if not isinstance(scenes_raw, list) or not scenes_raw:
        raise ValueError("scenes must be a non-empty list")

    scenes: list[SceneConfig] = []
    total_scene_duration = 0.0
    for idx, scene in enumerate(scenes_raw):
        text = str(scene.get("text", "")).strip()
        duration = float(scene.get("duration", 0))
        if not text:
            raise ValueError(f"scene[{idx}] text must not be empty")
        if duration <= 0:
            raise ValueError(f"scene[{idx}] duration must be > 0")
        scenes.append(SceneConfig(text=text, duration=duration))
        total_scene_duration += duration

    if total_scene_duration > duration_seconds + 1e-9:
        raise ValueError("sum of scene durations cannot exceed duration_seconds")

    voice_raw = raw.get("voiceover", {})
    voiceover = VoiceoverConfig(
        enabled=bool(voice_raw.get("enabled", False)),
        provider=str(voice_raw.get("provider", "")),
        audio_path=str(voice_raw.get("audio_path", "")),
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
