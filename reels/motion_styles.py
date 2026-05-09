from __future__ import annotations

from dataclasses import dataclass


@dataclass(frozen=True)
class MotionPreset:
    zoom_start: float
    zoom_end: float
    pan_x: float
    pan_y: float
    transition: str


MOTION_PRESETS = {
    "controlled": MotionPreset(1.02, 1.12, 0.03, -0.02, "push"),
    "urgent": MotionPreset(1.05, 1.18, -0.04, 0.03, "whip"),
    "reflective": MotionPreset(1.0, 1.08, 0.015, 0.015, "fade_blur"),
}


def choose_motion(text: str) -> MotionPreset:
    lower = text.lower()
    if any(k in lower for k in ["panic", "revenge", "overtrade", "loss"]):
        return MOTION_PRESETS["urgent"]
    if any(k in lower for k in ["discipline", "rules", "validate", "risk"]):
        return MOTION_PRESETS["controlled"]
    return MOTION_PRESETS["reflective"]
