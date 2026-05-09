from __future__ import annotations

import argparse
import json
import os
from pathlib import Path

from reels.visuals import build_visual_prompt, resolve_visual_style, SUPPORTED_VISUAL_STYLES

DEFAULT_TONE = "direct"
DEFAULT_DURATION_SECONDS = 18
DEFAULT_SCENE_COUNT = 4
DEFAULT_TEMPLATE = "discipline"
DEFAULT_BRAND = "generic"

SUPPORTED_TEMPLATES = {"discipline", "mistake", "checklist", "myth", "before-after"}
SUPPORTED_BRANDS = {"generic", "xeanvi"}

TONE_STYLES = {
    "direct": "Keep it simple and rule-based.",
    "calm": "Slow down and follow your process.",
    "coach": "Train the habit, not the hype.",
}

BRAND_PACKS = {
    "generic": {
        "default_audience": "retail traders",
        "default_cta": "Save this and review your process before your next session.",
        "background": {"solid": "#101820", "gradient_start": "#101820", "gradient_end": "#1f4068"},
    },
    "xeanvi": {
        "default_audience": "active traders building rule-based execution",
        "default_cta": "Save this and tighten your trading playbook in your command center.",
        "background": {"solid": "#0d1321", "gradient_start": "#0d1321", "gradient_end": "#1d2d50"},
    },
}



BANNED_MARKETING_TERMS = [
    "guaranteed profit",
    "guaranteed profits",
    "guaranteed returns",
    "guaranteed",
    "passive income",
    "make money while you sleep",
    "get rich",
    "risk-free",
    "no risk",
    "signals that win",
    "win rate",
    "100% accurate",
    "easy money",
    "financial advice",
    "buy now",
    "sell now",
]


def _validate_compliance_text(text: str, field_name: str) -> None:
    normalized = text.lower()
    for phrase in BANNED_MARKETING_TERMS:
        if phrase in normalized:
            raise ValueError(f"{field_name} contains prohibited marketing/compliance phrase: {phrase}")


def _validate_storyboard_compliance(payload: dict) -> None:
    _validate_compliance_text(payload.get("title", ""), "topic")
    scenes = payload.get("scenes", [])
    for scene in scenes:
        _validate_compliance_text(scene.get("text", ""), "generated scene text")


def _validate_inputs(
    topic: str,
    duration_seconds: int,
    scene_count: int,
    background_type: str,
    output: Path,
    template: str = DEFAULT_TEMPLATE,
    brand: str = DEFAULT_BRAND,
    visual_style: str | None = None,
) -> None:
    if not topic or not topic.strip():
        raise ValueError("topic must not be empty")
    if scene_count < 2:
        raise ValueError("scene_count must be at least 2")
    if duration_seconds < scene_count * 2:
        raise ValueError("duration_seconds is too short for the requested scene_count")
    if background_type not in {"solid", "gradient"}:
        raise ValueError("background_type must be one of: solid, gradient")
    if template not in SUPPORTED_TEMPLATES:
        raise ValueError(f"unsupported template: {template}")
    if brand not in SUPPORTED_BRANDS:
        raise ValueError(f"unsupported brand: {brand}")
    if output.suffix.lower() != ".json":
        raise ValueError("output path must end with .json")
    resolve_visual_style(brand, visual_style)


def _template_lines(template: str, topic: str, audience: str, cta: str, brand: str) -> list[str]:
    hook = f"{audience.title()}: {topic.strip()}"
    if brand == "xeanvi":
        safe_process = "Use a trading playbook, paper test it, and enforce risk controls before execution."
    else:
        safe_process = "Use a repeatable plan, test it, and enforce risk controls before execution."

    if template == "discipline":
        return [hook, "Most traders break rules under pressure.", safe_process, cta]
    if template == "mistake":
        return [f"Mistake: {topic.strip()}", "It hurts consistency and adds emotional trades.", "Use scanning, validation, and rule-based execution instead.", cta]
    if template == "checklist":
        return [hook, "Checklist 1: Define entry, stop, and invalidation.", "Checklist 2: Validate setup conditions before action.", f"Checklist 3: Log execution quality. {cta}"]
    if template == "myth":
        return [f"Myth: {topic.strip()}", "This framing ignores risk and process quality.", "Better framing: outcomes follow disciplined execution over time.", cta]
    return ["Before: Emotional, impulsive entries.", "After: Rule-based entries with validation.", "What changes: cleaner risk controls and better execution quality.", cta]


def _fit_lines_to_scene_count(lines: list[str], scene_count: int) -> list[str]:
    if scene_count == len(lines):
        return lines
    if scene_count < len(lines):
        result = lines[: scene_count - 1]
        result.append(" ".join(lines[scene_count - 1 :]))
        return result

    result = lines[:-1]
    filler = [
        "Execution quality beats emotional reaction.",
        "Track decisions and refine your process.",
        "Risk controls protect long-term consistency.",
        "Discipline scales better than motivation.",
    ]
    while len(result) < scene_count - 1:
        result.append(filler[(len(result) - (len(lines) - 1)) % len(filler)])
    result.append(lines[-1])
    return result


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
    audience: str | None = None,
    tone: str = DEFAULT_TONE,
    call_to_action: str | None = None,
    duration_seconds: int = DEFAULT_DURATION_SECONDS,
    scene_count: int = DEFAULT_SCENE_COUNT,
    background_type: str = "gradient",
    template: str = DEFAULT_TEMPLATE,
    brand: str = DEFAULT_BRAND,
    visual_style: str | None = None,
) -> dict:
    _validate_inputs(topic, duration_seconds, scene_count, background_type, Path("storyboard.json"), template, brand, visual_style)

    pack = BRAND_PACKS[brand]
    audience = (audience or "").strip() or pack["default_audience"]
    call_to_action = (call_to_action or "").strip() or pack["default_cta"]

    _validate_compliance_text(topic, "topic")
    _validate_compliance_text(call_to_action, "call_to_action")

    title = f"{topic.strip()}"
    template_lines = _template_lines(template, topic, audience, call_to_action, brand)
    scene_texts = _fit_lines_to_scene_count(template_lines, scene_count)
    durations = _allocate_scene_durations(duration_seconds, scene_count)
    scenes = [{"text": text, "duration": duration} for text, duration in zip(scene_texts, durations)]

    bg = pack["background"]
    background = {"type": background_type, "color": bg["gradient_start"], "color_end": bg["gradient_end"]}
    if background_type == "solid":
        background["color"] = bg["solid"]
        background["color_end"] = bg["solid"]

    style = resolve_visual_style(brand, visual_style)
    visual = build_visual_prompt(style=style, brand=brand, topic=topic)

    payload = {
        "title": title,
        "duration_seconds": duration_seconds,
        "size": [1080, 1920],
        "fps": 24,
        "background": background,
        "scenes": scenes,
        "voiceover": {"enabled": False, "provider": "", "audio_path": ""},
        "visual": {
            "style": visual.style,
            "image_prompt": visual.image_prompt,
            "negative_prompt": visual.negative_prompt,
            "background_role": "optional_ai_or_manual_background",
        },
    }
    _validate_storyboard_compliance(payload)
    return payload


def main() -> int:
    parser = argparse.ArgumentParser(description="Generate reel storyboard JSON from a topic")
    parser.add_argument("--topic", required=True, help="Reel topic/angle")
    parser.add_argument("--audience", default=None, help="Target audience")
    parser.add_argument("--tone", default=DEFAULT_TONE, help="Tone style")
    parser.add_argument("--call-to-action", default=None)
    parser.add_argument("--duration-seconds", type=int, default=DEFAULT_DURATION_SECONDS)
    parser.add_argument("--scene-count", type=int, default=DEFAULT_SCENE_COUNT)
    parser.add_argument("--background-type", default="gradient", help="solid or gradient")
    parser.add_argument("--template", default=DEFAULT_TEMPLATE, choices=sorted(SUPPORTED_TEMPLATES))
    parser.add_argument("--brand", default=DEFAULT_BRAND, choices=sorted(SUPPORTED_BRANDS))
    parser.add_argument("--visual-style", default=None, choices=sorted(SUPPORTED_VISUAL_STYLES), help="Optional visual style override")
    parser.add_argument("--output", required=True, help="Output JSON path")
    args = parser.parse_args()

    output = Path(args.output)
    try:
        _validate_inputs(args.topic, args.duration_seconds, args.scene_count, args.background_type, output, args.template, args.brand, args.visual_style)

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
                template=args.template,
                brand=args.brand,
                visual_style=args.visual_style,
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
                template=args.template,
                brand=args.brand,
                visual_style=args.visual_style,
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
