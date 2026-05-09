from __future__ import annotations

from dataclasses import dataclass


@dataclass(frozen=True)
class ReelTemplate:
    name: str
    beats: list[tuple[str, float, float]]


TEMPLATES = {
    "punchy_problem_solution": ReelTemplate(
        name="punchy_problem_solution",
        beats=[("hook", 0.0, 1.5), ("problem", 1.5, 5.0), ("solution", 5.0, 10.5), ("cta", 10.5, 13.0)],
    ),
    "mistake_breakdown": ReelTemplate(
        name="mistake_breakdown",
        beats=[("hook", 0.0, 2.0), ("consequence", 2.0, 5.0), ("instead", 5.0, 9.5), ("cta", 9.5, 12.0)],
    ),
    "discipline_engine": ReelTemplate(
        name="discipline_engine",
        beats=[("bold", 0.0, 1.5), ("contrast", 1.5, 4.5), ("process", 4.5, 9.0), ("cta", 9.0, 12.0)],
    ),
}


def clamp_duration(duration_seconds: float) -> float:
    return max(8.0, min(15.0, float(duration_seconds)))
