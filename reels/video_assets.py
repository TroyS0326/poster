from __future__ import annotations

import json
from dataclasses import dataclass
from pathlib import Path


@dataclass(frozen=True)
class VideoClipAsset:
    id: str
    path: str
    tags: tuple[str, ...]
    mood: str = "neutral"
    safe_for: tuple[str, ...] = ()


KEYWORD_TAGS = {
    "revenge": ["mistake", "stress", "risk", "overtrading", "red"],
    "overtrading": ["clutter", "screens", "speed", "stress"],
    "paper": ["journal", "simulator", "practice", "calm"],
    "execution": ["checklist", "discipline", "focus", "system", "rules"],
    "risk": ["risk", "chart", "stop", "structure", "red", "green"],
    "automation": ["dashboard", "scanning", "workflow", "system"],
}


class VideoManifestError(ValueError):
    pass


def load_video_manifest(path: str | Path) -> list[VideoClipAsset]:
    p = Path(path)
    if not p.exists():
        raise VideoManifestError("video renderer requires a valid video manifest with at least one usable clip")
    raw = json.loads(p.read_text(encoding="utf-8"))
    clips = []
    for c in raw.get("clips", []):
        cp = Path(str(c.get("path", "")))
        if not cp.exists():
            continue
        clips.append(VideoClipAsset(
            id=str(c.get("id", "")).strip(),
            path=str(cp),
            tags=tuple(t.lower() for t in c.get("tags", [])),
            mood=str(c.get("mood", "neutral")).lower(),
            safe_for=tuple(t.lower() for t in c.get("safe_for", [])),
        ))
    if not clips:
        raise VideoManifestError("video renderer requires a valid video manifest with at least one usable clip")
    return clips


def select_clip(clips: list[VideoClipAsset], *, topic: str, scene_text: str, template: str, tone: str) -> VideoClipAsset:
    hay = f"{topic} {scene_text} {template} {tone}".lower()
    desired = []
    for k, tags in KEYWORD_TAGS.items():
        if k in hay:
            desired.extend(tags)
    best = None
    best_score = -1
    for c in clips:
        score = sum(3 for t in desired if t in c.tags)
        score += sum(2 for t in desired if t in c.safe_for)
        score += sum(1 for t in c.tags if t in hay)
        if tone and tone in ("stress", "mistake") and "red" in c.tags:
            score += 2
        if tone and tone in ("discipline", "process") and any(x in c.tags for x in ("discipline", "focus", "system")):
            score += 2
        if score > best_score:
            best, best_score = c, score
    return best or clips[0]
