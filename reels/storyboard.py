from __future__ import annotations
import argparse, json, os, re
from pathlib import Path
from reels.backgrounds import generate_background_png
from reels.compliance import validate_compliance_text
from reels.visuals import (SUPPORTED_VISUAL_BRANDS, SUPPORTED_VISUAL_STYLES,
    build_visual_prompt, resolve_visual_style)

DEFAULT_TONE = "direct"
DEFAULT_DURATION_SECONDS = 18
DEFAULT_SCENE_COUNT = 4
DEFAULT_TEMPLATE = "discipline"
DEFAULT_BRAND = "generic"
SUPPORTED_TEMPLATES = {"discipline", "mistake", "checklist", "myth", "before-after"}
SUPPORTED_BRANDS = SUPPORTED_VISUAL_BRANDS
SUPPORTED_VOICEOVER_AUDIO_EXTENSIONS = {".mp3", ".wav", ".m4a", ".aac"}

BRAND_PACKS = {
    "generic": {
        "default_audience": "retail traders",
        "default_cta": "Save this and review your process before your next session.",
        "background": {"solid": "#101820", "gradient_start": "#101820", "gradient_end": "#1f4068"},
    },
    "xeanvi": {
        "default_audience": "active traders building rule-based execution",
        "default_cta": "Save this. Your future self will thank you.",
        "background": {"solid": "#0d1321", "gradient_start": "#0d1321", "gradient_end": "#1d2d50"},
    },
}

def _validate_storyboard_compliance(payload: dict) -> None:
    validate_compliance_text(payload.get("title", ""), "topic")
    for scene in payload.get("scenes", []):
        validate_compliance_text(scene.get("text", ""), "generated scene text")
    script = str(payload.get("voiceover", {}).get("script", "")).strip()
    if script:
        validate_compliance_text(script, "voiceover.script")

def _validate_voiceover_audio_path(audio_path: str) -> None:
    ext = Path(audio_path).suffix.lower()
    if ext not in SUPPORTED_VOICEOVER_AUDIO_EXTENSIONS:
        raise ValueError("voiceover audio path must end with .mp3, .wav, .m4a, or .aac")

def _validate_inputs(topic, duration_seconds, scene_count, background_type, output,
                     template=DEFAULT_TEMPLATE, brand=DEFAULT_BRAND, visual_style=None):
    if not topic or not topic.strip(): raise ValueError("topic must not be empty")
    if scene_count < 2: raise ValueError("scene_count must be at least 2")
    if duration_seconds < scene_count * 2: raise ValueError("duration_seconds is too short for the requested scene_count")
    if background_type not in {"solid", "gradient"}: raise ValueError("background_type must be one of: solid, gradient")
    if template not in SUPPORTED_TEMPLATES: raise ValueError(f"unsupported template: {template}")
    if brand not in SUPPORTED_BRANDS: raise ValueError(f"unsupported brand: {brand}")
    if output.suffix.lower() != ".json": raise ValueError("output path must end with .json")
    resolve_visual_style(brand, visual_style)

def _allocate_scene_durations(duration_seconds, scene_count):
    base = round(duration_seconds / scene_count, 2)
    durations = [base] * scene_count
    allocated = round(base * (scene_count - 1), 2)
    durations[-1] = round(duration_seconds - allocated, 2)
    if durations[-1] <= 0:
        total_cents = int(round(duration_seconds * 100))
        base_cents, remainder = divmod(total_cents, scene_count)
        durations = [base_cents / 100.0] * scene_count
        durations[-1] = (base_cents + remainder) / 100.0
    return durations

def _fit_lines_to_scene_count(lines, scene_count):
    if scene_count == len(lines): return lines
    if scene_count < len(lines):
        result = lines[:scene_count - 1]
        result.append(" ".join(lines[scene_count - 1:]))
        return result
    result = lines[:-1]
    filler = ["Execution quality beats emotional reaction.",
              "Track decisions and refine your process.",
              "Risk controls protect long-term consistency.",
              "Discipline scales better than motivation."]
    while len(result) < scene_count - 1:
        result.append(filler[(len(result) - (len(lines) - 1)) % len(filler)])
    result.append(lines[-1])
    return result

def _template_lines(template, topic, audience, cta, brand):
    hook = f"{audience.title()}: {topic.strip()}"
    safe_process = "Use a trading playbook, paper test it, and enforce risk controls before execution." if brand == "xeanvi" else "Use a repeatable plan, test it, and enforce risk controls before execution."
    if template == "discipline":
        return [hook, "Most traders break rules under pressure.", safe_process, cta]
    if template == "mistake":
        return [f"Mistake: {topic.strip()}", "It hurts consistency and adds emotional trades.", "Use scanning, validation, and rule-based execution instead.", cta]
    if template == "checklist":
        return [hook, "Checklist 1: Define entry, stop, and invalidation.", "Checklist 2: Validate setup conditions before action.", f"Checklist 3: Log execution quality. {cta}"]
    if template == "myth":
        return [f"Myth: {topic.strip()}", "This framing ignores risk and process quality.", "Better framing: outcomes follow disciplined execution over time.", cta]
    return ["Before: Emotional, impulsive entries.", "After: Rule-based entries with validation.", "What changes: cleaner risk controls and better execution quality.", cta]

def generate_storyboard(topic, audience=None, tone=DEFAULT_TONE, call_to_action=None,
                        duration_seconds=DEFAULT_DURATION_SECONDS, scene_count=DEFAULT_SCENE_COUNT,
                        background_type="gradient", template=DEFAULT_TEMPLATE, brand=DEFAULT_BRAND,
                        visual_style=None, background_image_path=None,
                        include_voiceover_script=False, voiceover_audio_path=None):
    _validate_inputs(topic, duration_seconds, scene_count, background_type,
                     Path("storyboard.json"), template, brand, visual_style)
    if background_image_path and not background_image_path.lower().endswith(".png"):
        raise ValueError("background_image_path must end with .png")

    pack = BRAND_PACKS[brand]
    audience = (audience or "").strip() or pack["default_audience"]
    call_to_action = (call_to_action or "").strip() or pack["default_cta"]
    validate_compliance_text(topic, "topic")
    validate_compliance_text(call_to_action, "call_to_action")

    # Try Gemini-powered script first
    ai_script = None
    try:
        from reels.script_writer import generate_reel_script
        ai_script = generate_reel_script(topic)
    except Exception:
        pass

    if ai_script:
        scene_texts = [
            ai_script["hook"],
            ai_script["problem"],
            ai_script["insight"],
            ai_script["cta"],
        ]
        scene_texts = _fit_lines_to_scene_count(scene_texts, scene_count)
        voiceover_script = ai_script.get("voiceover", "")
    else:
        template_lines = _template_lines(template, topic, audience, call_to_action, brand)
        scene_texts = _fit_lines_to_scene_count(template_lines, scene_count)
        joined = ". ".join(t.strip().rstrip(".") for t in scene_texts)
        voiceover_script = f"{joined}." if (include_voiceover_script or voiceover_audio_path) else ""

    durations = _allocate_scene_durations(duration_seconds, scene_count)
    # Strip pause markers from scene text (they belong in voiceover only)
    import re as _re
    def _clean(t):
        t = _re.sub(r"\((?:short |long )?pause\)", " ", t, flags=_re.I)
        t = _re.sub(r"\[(?:short |long )?pause\]", " ", t, flags=_re.I)
        return _re.sub(r"\s{2,}", " ", t).strip()
    scenes = [{"text": _clean(text), "duration": dur} for text, dur in zip(scene_texts, durations)]

    if voiceover_audio_path:
        _validate_voiceover_audio_path(voiceover_audio_path)

    bg = pack["background"]
    if background_image_path:
        background = {"type": "image", "path": background_image_path}
    else:
        background = {"type": background_type, "color": bg["gradient_start"], "color_end": bg["gradient_end"]}
        if background_type == "solid":
            background["color"] = bg["solid"]; background["color_end"] = bg["solid"]

    style = resolve_visual_style(brand, visual_style)
    visual = build_visual_prompt(style=style, brand=brand, topic=topic)

    payload = {
        "title": topic.strip(),
        "duration_seconds": duration_seconds,
        "size": [1080, 1920],
        "fps": 24,
        "background": background,
        "scenes": scenes,
        "voiceover": {
            "enabled": bool(voiceover_audio_path),
            "provider": "local_audio" if voiceover_audio_path else "",
            "audio_path": voiceover_audio_path or "",
            "script": voiceover_script,
        },
        "visual": {
            "style": visual.style,
            "image_prompt": visual.image_prompt,
            "negative_prompt": visual.negative_prompt,
            "background_role": "optional_ai_or_manual_background",
        },
    }
    _validate_storyboard_compliance(payload)
    return payload

def _safe_background_basename(brand, template, visual_style, topic, max_length=120):
    raw = f"{brand}_{template}_{visual_style}_{topic}".lower().strip()
    slug = re.sub(r"\s+", "_", raw)
    slug = re.sub(r"[^a-z0-9_]+", "", slug)
    slug = re.sub(r"_+", "_", slug).strip("_")
    return slug[:max_length].rstrip("_") or "background"

def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--topic", required=True)
    parser.add_argument("--audience", default=None)
    parser.add_argument("--tone", default=DEFAULT_TONE)
    parser.add_argument("--call-to-action", default=None)
    parser.add_argument("--duration-seconds", type=int, default=DEFAULT_DURATION_SECONDS)
    parser.add_argument("--scene-count", type=int, default=DEFAULT_SCENE_COUNT)
    parser.add_argument("--background-type", default="gradient")
    parser.add_argument("--template", default=DEFAULT_TEMPLATE, choices=sorted(SUPPORTED_TEMPLATES))
    parser.add_argument("--brand", default=DEFAULT_BRAND, choices=sorted(SUPPORTED_BRANDS))
    parser.add_argument("--visual-style", default=None, choices=sorted(SUPPORTED_VISUAL_STYLES))
    parser.add_argument("--generate-background", action="store_true")
    parser.add_argument("--background-output", default=None)
    parser.add_argument("--output", required=True)
    parser.add_argument("--voiceover-script", action="store_true")
    parser.add_argument("--voiceover-audio", default=None)
    args = parser.parse_args()
    output = Path(args.output)
    try:
        _validate_inputs(args.topic, args.duration_seconds, args.scene_count,
                         args.background_type, output, args.template, args.brand, args.visual_style)
        resolved_style = resolve_visual_style(args.brand, args.visual_style)
        background_image_path = None
        if args.background_output and not args.generate_background:
            raise ValueError("background-output requires --generate-background")
        if args.generate_background:
            bg_out = Path(args.background_output) if args.background_output else Path("outputs/backgrounds") / f"{_safe_background_basename(args.brand, args.template, resolved_style, args.topic)}.png"
            generate_background_png(style=resolved_style, brand=args.brand, output=bg_out)
            background_image_path = str(bg_out)
        storyboard = generate_storyboard(
            topic=args.topic, audience=args.audience, tone=args.tone,
            call_to_action=args.call_to_action, duration_seconds=args.duration_seconds,
            scene_count=args.scene_count, background_type=args.background_type,
            template=args.template, brand=args.brand, visual_style=args.visual_style,
            background_image_path=background_image_path,
            include_voiceover_script=args.voiceover_script,
            voiceover_audio_path=args.voiceover_audio)
        output.parent.mkdir(parents=True, exist_ok=True)
        output.write_text(json.dumps(storyboard, indent=2), encoding="utf-8")
    except ValueError as exc:
        print(f"ERROR: {exc}"); return 2
    print(f"Storyboard JSON generated: {output.resolve()}")
    return 0

if __name__ == "__main__":
    raise SystemExit(main())
