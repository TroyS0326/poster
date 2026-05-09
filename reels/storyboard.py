from __future__ import annotations

import argparse
import json
import os
from pathlib import Path

DEFAULT_AUDIENCE = "retail day traders"
DEFAULT_TONE = "direct"
DEFAULT_DURATION_SECONDS = 18
DEFAULT_SCENE_COUNT = 4

TONE_STYLES = {
    "direct": "Keep it simple and rule-based.",
    "calm": "Slow down and follow your process.",
    "coach": "Train the habit, not the hype.",
}


def _validate_inputs(
    topic: str,
    duration_seconds: int,
    scene_count: int,
    background_type: str,
    output: Path,
) -> None:
    if not topic or not topic.strip():
        raise ValueError("topic must not be empty")
    if scene_count < 2:
        raise ValueError("scene_count must be at least 2")
    if duration_seconds < scene_count * 2:
        raise ValueError("duration_seconds is too short for the requested scene_count")
    if background_type not in {"solid", "gradient"}:
        raise ValueError("background_type must be one of: solid, gradient")
    if output.suffix.lower() != ".json":
        raise ValueError("output path must end with .json")


def _build_scene_texts(topic: str, audience: str, tone: str, call_to_action: str, scene_count: int) -> list[str]:
    hook = f"{audience.title()}: {topic.strip()}"
    problem = "Most traders break rules under pressure, then call it strategy."
    insight = "Build a playbook, paper test it, and follow risk limits before emotion takes over."
    cta = call_to_action.strip() or "Save this and review your rules before your next session."

    if scene_count == 2:
        return [hook, f"{insight} {cta}"]

    if scene_count == 3:
        return [hook, problem, f"{insight} {cta}"]

    scenes = [hook, problem]
    middle_count = scene_count - 3
    middle_lines = [
        insight,
        "Discipline is execution quality, not motivation.",
        "Risk controls and emotional control protect your edge.",
        TONE_STYLES.get(tone, TONE_STYLES["direct"]),
    ]
    for idx in range(middle_count):
        scenes.append(middle_lines[idx % len(middle_lines)])
    scenes.append(cta)
    return scenes


def _allocate_scene_durations(duration_seconds: int, scene_count: int) -> list[float]:
    base = round(duration_seconds / scene_count, 2)
    durations = [base] * scene_count
    allocated = round(base * (scene_count - 1), 2)
    durations[-1] = round(duration_seconds - allocated, 2)

    if durations[-1] <= 0:
        # Safety fallback: distribute in centiseconds and convert back.
        total_cents = int(round(duration_seconds * 100))
        base_cents, remainder = divmod(total_cents, scene_count)
        durations = [base_cents / 100.0] * scene_count
        durations[-1] = (base_cents + remainder) / 100.0

    return durations


def generate_storyboard(
    topic: str,
    audience: str = DEFAULT_AUDIENCE,
    tone: str = DEFAULT_TONE,
    call_to_action: str = "Save this and tighten your trading playbook.",
    duration_seconds: int = DEFAULT_DURATION_SECONDS,
    scene_count: int = DEFAULT_SCENE_COUNT,
    background_type: str = "gradient",
) -> dict:
    _validate_inputs(topic, duration_seconds, scene_count, background_type, Path("storyboard.json"))

    title = f"{topic.strip()}"
    scene_texts = _build_scene_texts(topic, audience, tone, call_to_action, scene_count)
    durations = _allocate_scene_durations(duration_seconds, scene_count)
    scenes = [{"text": text, "duration": duration} for text, duration in zip(scene_texts, durations)]

    background = {"type": background_type, "color": "#101820", "color_end": "#1f4068"}
    if background_type == "solid":
        background["color"] = "#101820"
        background["color_end"] = "#101820"

    return {
        "title": title,
        "duration_seconds": duration_seconds,
        "size": [1080, 1920],
        "fps": 24,
        "background": background,
        "scenes": scenes,
        "voiceover": {"enabled": False, "provider": "", "audio_path": ""},
    }


def main() -> int:
    parser = argparse.ArgumentParser(description="Generate reel storyboard JSON from a topic")
    parser.add_argument("--topic", required=True, help="Reel topic/angle")
    parser.add_argument("--audience", default=DEFAULT_AUDIENCE, help="Target audience")
    parser.add_argument("--tone", default=DEFAULT_TONE, help="Tone style")
    parser.add_argument("--call-to-action", default="Save this and tighten your trading playbook.")
    parser.add_argument("--duration-seconds", type=int, default=DEFAULT_DURATION_SECONDS)
    parser.add_argument("--scene-count", type=int, default=DEFAULT_SCENE_COUNT)
    parser.add_argument("--background-type", default="gradient", help="solid or gradient")
    parser.add_argument("--output", required=True, help="Output JSON path")
    args = parser.parse_args()

    output = Path(args.output)
    try:
        _validate_inputs(args.topic, args.duration_seconds, args.scene_count, args.background_type, output)

        ai_provider = os.getenv("REELS_STORYBOARD_AI_PROVIDER", "").strip()
        if ai_provider:
            # Future-safe switch; local mode remains default/non-breaking.
            storyboard = generate_storyboard(
                topic=args.topic,
                audience=args.audience,
                tone=args.tone,
                call_to_action=args.call_to_action,
                duration_seconds=args.duration_seconds,
                scene_count=args.scene_count,
                background_type=args.background_type,
            )
        else:
            storyboard = generate_storyboard(
                topic=args.topic,
                audience=args.audience,
                tone=args.tone,
                call_to_action=args.call_to_action,
                duration_seconds=args.duration_seconds,
                scene_count=args.scene_count,
                background_type=args.background_type,
            )

        output.parent.mkdir(parents=True, exist_ok=True)
        output.write_text(json.dumps(storyboard, indent=2), encoding="utf-8")
    except ValueError as exc:
        print(f"ERROR: {exc}")
        return 2

    print(f"Storyboard JSON generated: {output.resolve()}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
