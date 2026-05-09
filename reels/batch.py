from __future__ import annotations

import argparse
import json
import re
from pathlib import Path
from typing import Any

from reels.backgrounds import generate_background_png
from reels.compliance import validate_compliance_text
from reels.config import load_reel_config
from reels.generate import render_reel
from reels.storyboard import (
    DEFAULT_BRAND,
    DEFAULT_DURATION_SECONDS,
    DEFAULT_SCENE_COUNT,
    DEFAULT_TEMPLATE,
    generate_storyboard,
)
from reels.visuals import resolve_visual_style
from reels.voiceover import write_silent_wav


def _slugify(value: str) -> str:
    slug = re.sub(r"\s+", "_", value.strip().lower())
    slug = re.sub(r"[^a-z0-9_\-]+", "", slug)
    slug = re.sub(r"[_\-]+", "_", slug).strip("_")
    return slug


def _ensure_bool(value: Any, field_name: str) -> bool:
    if not isinstance(value, bool):
        raise ValueError(f"{field_name} must be a boolean")
    return value


def _int_or_raise(value: Any, field_name: str) -> int:
    try:
        return int(value)
    except (TypeError, ValueError) as exc:
        raise ValueError(f"{field_name} must be numeric") from exc


def load_batch_input(path: Path) -> dict[str, Any]:
    if not path.exists():
        raise FileNotFoundError(f"batch input file not found: {path}")
    try:
        payload = json.loads(path.read_text(encoding="utf-8"))
    except json.JSONDecodeError as exc:
        raise ValueError(f"invalid JSON in {path}: {exc}") from exc
    if not isinstance(payload, dict):
        raise ValueError("batch input must be an object")
    return payload


def _merge_item_defaults(defaults: dict[str, Any], item: dict[str, Any]) -> dict[str, Any]:
    merged = dict(defaults)
    merged.update(item)
    return merged


def run_batch(payload: dict[str, Any], output_dir: Path) -> dict[str, Any]:
    output_dir.mkdir(parents=True, exist_ok=True)

    items = payload.get("items")
    if not isinstance(items, list) or not items:
        raise ValueError("items must be a non-empty list")

    defaults = {
        "brand": payload.get("brand", DEFAULT_BRAND),
        "template": payload.get("template", DEFAULT_TEMPLATE),
        "visual_style": payload.get("visual_style"),
        "duration_seconds": _int_or_raise(payload.get("duration_seconds", DEFAULT_DURATION_SECONDS), "duration_seconds"),
        "scene_count": _int_or_raise(payload.get("scene_count", DEFAULT_SCENE_COUNT), "scene_count"),
        "generate_background": _ensure_bool(payload.get("generate_background", False), "generate_background"),
        "generate_voiceover_placeholder": _ensure_bool(
            payload.get("generate_voiceover_placeholder", False), "generate_voiceover_placeholder"
        ),
        "render_mp4": _ensure_bool(payload.get("render_mp4", False), "render_mp4"),
    }

    seen_slugs: set[str] = set()
    summary_items: list[dict[str, Any]] = []

    for idx, raw_item in enumerate(items):
        entry: dict[str, Any] = {"index": idx, "status": "success"}
        try:
            if not isinstance(raw_item, dict):
                raise ValueError(f"items[{idx}] must be an object")

            merged = _merge_item_defaults(defaults, raw_item)
            topic = str(merged.get("topic", "")).strip()
            if not topic:
                raise ValueError(f"items[{idx}].topic must be non-empty")
            validate_compliance_text(topic, f"items[{idx}].topic")

            slug = str(merged.get("slug", "")).strip() or _slugify(topic)
            slug = _slugify(slug)
            if not slug:
                raise ValueError(f"items[{idx}] slug is empty after sanitization")
            if slug in seen_slugs:
                raise ValueError(f"duplicate slug detected: {slug}")
            seen_slugs.add(slug)

            generate_background = _ensure_bool(merged.get("generate_background", False), f"items[{idx}].generate_background")
            generate_voiceover_placeholder = _ensure_bool(
                merged.get("generate_voiceover_placeholder", False), f"items[{idx}].generate_voiceover_placeholder"
            )
            render_mp4 = _ensure_bool(merged.get("render_mp4", False), f"items[{idx}].render_mp4")
            duration_seconds = _int_or_raise(merged.get("duration_seconds"), f"items[{idx}].duration_seconds")
            scene_count = _int_or_raise(merged.get("scene_count"), f"items[{idx}].scene_count")
            brand = str(merged.get("brand"))
            visual_style = merged.get("visual_style")

            item_dir = output_dir / slug
            item_dir.mkdir(parents=True, exist_ok=True)
            json_path = item_dir / f"{slug}.json"
            png_path = item_dir / f"{slug}.png"
            wav_path = item_dir / f"{slug}.wav"
            mp4_path = item_dir / f"{slug}.mp4"

            voiceover_audio_path = str(wav_path) if generate_voiceover_placeholder else None
            background_image_path = str(png_path) if generate_background else None

            resolved_style = resolve_visual_style(brand, visual_style)
            if generate_background:
                generate_background_png(style=resolved_style, brand=brand, output=png_path)
                entry["png_path"] = str(png_path)
                storyboard = generate_storyboard(
                    topic=topic,
                    duration_seconds=duration_seconds,
                    scene_count=scene_count,
                    template=str(merged.get("template")),
                    brand=brand,
                    visual_style=resolved_style,
                    background_image_path=background_image_path,
                    include_voiceover_script=generate_voiceover_placeholder,
                    voiceover_audio_path=voiceover_audio_path,
                )
            else:
                storyboard = generate_storyboard(
                    topic=topic,
                    duration_seconds=duration_seconds,
                    scene_count=scene_count,
                    template=str(merged.get("template")),
                    brand=brand,
                    visual_style=resolved_style,
                    background_image_path=background_image_path,
                    include_voiceover_script=generate_voiceover_placeholder,
                    voiceover_audio_path=voiceover_audio_path,
                )
            json_path.write_text(json.dumps(storyboard, indent=2), encoding="utf-8")
            entry["slug"] = slug
            entry["topic"] = topic
            entry["json_path"] = str(json_path)

            if generate_voiceover_placeholder:
                cfg = load_reel_config(json_path)
                write_silent_wav(wav_path, cfg.duration_seconds)
                entry["wav_path"] = str(wav_path)

            if render_mp4:
                try:
                    render_reel(load_reel_config(json_path), mp4_path)
                    entry["mp4_path"] = str(mp4_path)
                except RuntimeError as exc:
                    entry["status"] = "render_failed"
                    entry["error"] = str(exc)
            summary_items.append(entry)
        except Exception as exc:
            entry.setdefault("slug", _slugify(str(raw_item.get("slug", ""))) if isinstance(raw_item, dict) else "")
            if isinstance(raw_item, dict):
                topic = str(raw_item.get("topic", "")).strip()
                if topic:
                    entry["topic"] = topic
            entry["status"] = "failed"
            entry["error"] = str(exc)
            summary_items.append(entry)

    summary = {"output_dir": str(output_dir), "items": summary_items}
    (output_dir / "summary.json").write_text(json.dumps(summary, indent=2), encoding="utf-8")
    return summary


def _print_summary(summary: dict[str, Any]) -> None:
    for item in summary["items"]:
        slug = item.get("slug") or f"index_{item.get('index')}"
        parts = [f"slug={slug}", f"status={item.get('status')}"]
        for key in ("json_path", "png_path", "wav_path", "mp4_path"):
            if item.get(key):
                parts.append(f"{key}={item[key]}")
        if item.get("error"):
            parts.append(f"error={item['error']}")
        print(" | ".join(parts))


def main() -> int:
    parser = argparse.ArgumentParser(description="Batch reels workflow from JSON items")
    parser.add_argument("--input", required=True, help="Batch JSON input path")
    parser.add_argument("--output-dir", required=True, help="Directory for batch outputs")
    args = parser.parse_args()
    try:
        payload = load_batch_input(Path(args.input))
        summary = run_batch(payload, Path(args.output_dir))
    except (FileNotFoundError, ValueError) as exc:
        print(f"ERROR: {exc}")
        return 2

    _print_summary(summary)
    print(f"summary_path={Path(args.output_dir) / 'summary.json'}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
