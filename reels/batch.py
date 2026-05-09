from __future__ import annotations

import argparse
import json
import re
from datetime import datetime, timezone
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
from reels.tts import get_provider
from reels.scene_images import generate_scene_images


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
    if isinstance(value, bool):
        raise ValueError(f"{field_name} must be numeric")
    try:
        return int(value)
    except (TypeError, ValueError) as exc:
        raise ValueError(f"{field_name} must be numeric") from exc


def _validate_timing(duration_seconds: int, scene_count: int, field_prefix: str) -> None:
    duration_field = f"{field_prefix}.duration_seconds" if field_prefix else "duration_seconds"
    scene_field = f"{field_prefix}.scene_count" if field_prefix else "scene_count"
    if duration_seconds <= 0:
        raise ValueError(f"{duration_field} must be > 0")
    if scene_count < 2:
        raise ValueError(f"{scene_field} must be at least 2")
    if duration_seconds < scene_count * 2:
        raise ValueError(f"{duration_field} is too short for the requested scene_count")


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


def _utc_timestamp() -> str:
    return datetime.now(timezone.utc).isoformat()


def _write_event(log_path: Path, event_dict: dict[str, Any]) -> None:
    payload = dict(event_dict)
    payload.setdefault("timestamp", _utc_timestamp())
    with log_path.open("a", encoding="utf-8") as handle:
        handle.write(json.dumps(payload) + "\n")


def _build_summary(output_dir: Path, items: list[dict[str, Any]]) -> dict[str, Any]:
    success_count = sum(1 for item in items if item.get("status") == "success")
    failed_count = sum(1 for item in items if item.get("status") == "failed")
    render_failed_count = sum(1 for item in items if item.get("status") == "render_failed")
    return {
        "output_dir": str(output_dir),
        "total_items": len(items),
        "success_count": success_count,
        "failed_count": failed_count,
        "render_failed_count": render_failed_count,
        "items": items,
    }


def _normalize_voiceover_format(value: Any, *, field_name: str) -> str | None:
    if value is None:
        return None
    if not isinstance(value, str):
        raise ValueError(f"{field_name} must be one of: wav, mp3")
    normalized = value.strip().lower()
    if not normalized:
        return None
    if normalized not in {"wav", "mp3"}:
        raise ValueError(f"{field_name} must be one of: wav, mp3")
    return normalized


def _build_defaults(payload: dict[str, Any]) -> dict[str, Any]:
    duration_seconds = _int_or_raise(payload.get("duration_seconds", DEFAULT_DURATION_SECONDS), "duration_seconds")
    scene_count = _int_or_raise(payload.get("scene_count", DEFAULT_SCENE_COUNT), "scene_count")
    _validate_timing(duration_seconds, scene_count, "")
    return {
        "brand": payload.get("brand", DEFAULT_BRAND),
        "template": payload.get("template", DEFAULT_TEMPLATE),
        "visual_style": payload.get("visual_style"),
        "duration_seconds": duration_seconds,
        "scene_count": scene_count,
        "generate_background": _ensure_bool(payload.get("generate_background", False), "generate_background"),
        "generate_voiceover_placeholder": _ensure_bool(
            payload.get("generate_voiceover_placeholder", False), "generate_voiceover_placeholder"
        ),
        "render_mp4": _ensure_bool(payload.get("render_mp4", False), "render_mp4"),
        "voiceover_provider": str(payload.get("voiceover_provider", "silent")),
        "voiceover_voice": payload.get("voiceover_voice"),
        "voiceover_format": payload.get("voiceover_format"),
    }


def plan_batch(payload: dict[str, Any], output_dir: Path) -> dict[str, Any]:
    items = payload.get("items")
    if not isinstance(items, list) or not items:
        raise ValueError("items must be a non-empty list")
    defaults = _build_defaults(payload)

    seen_slugs: set[str] = set()
    planned_items: list[dict[str, Any]] = []
    for idx, raw_item in enumerate(items):
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

        _ensure_bool(merged.get("generate_background", False), f"items[{idx}].generate_background")
        generate_voiceover_placeholder = _ensure_bool(
            merged.get("generate_voiceover_placeholder", False), f"items[{idx}].generate_voiceover_placeholder"
        )
        _ensure_bool(merged.get("render_mp4", False), f"items[{idx}].render_mp4")
        duration_seconds = _int_or_raise(merged.get("duration_seconds"), f"items[{idx}].duration_seconds")
        scene_count = _int_or_raise(merged.get("scene_count"), f"items[{idx}].scene_count")
        _validate_timing(duration_seconds, scene_count, f"items[{idx}]")
        brand = str(merged.get("brand"))
        visual_style = merged.get("visual_style")
        resolve_visual_style(brand, visual_style)
        template = str(merged.get("template"))
        if template not in {"discipline", "mistake", "checklist", "myth", "before-after"}:
            raise ValueError(f"items[{idx}].template must be one of: discipline, mistake, checklist, myth, before-after")

        voiceover_provider = str(merged.get("voiceover_provider", "silent"))
        voiceover_format = _normalize_voiceover_format(merged.get("voiceover_format"), field_name=f"items[{idx}].voiceover_format")
        final_audio_format = voiceover_format or "wav"
        if voiceover_provider == "silent" and final_audio_format != "wav":
            raise ValueError(f"items[{idx}].voiceover_format must be wav when voiceover_provider is silent")
        get_provider(voiceover_provider)

        item_dir = output_dir / slug
        planned_items.append(
            {
                "index": idx,
                "slug": slug,
                "topic": topic,
                "item_dir": str(item_dir),
                "json_path": str(item_dir / f"{slug}.json"),
                "png_path": str(item_dir / f"{slug}.png"),
                "audio_path": str(item_dir / f"{slug}.{final_audio_format}") if generate_voiceover_placeholder else None,
                "mp4_path": str(item_dir / f"{slug}.mp4"),
            }
        )
    return {"output_dir": str(output_dir), "item_count": len(items), "items": planned_items}


def _write_run_report(summary: dict[str, Any], report_path: Path) -> None:
    skipped_render_count = sum(
        1 for item in summary["items"] if item.get("status") == "success" and item.get("render_requested") is False
    )
    lines = [
        "# Batch Run Report",
        "",
        f"- run_timestamp: {_utc_timestamp()}",
        f"- output_directory: {summary['output_dir']}",
        f"- total_items: {summary['total_items']}",
        f"- success_count: {summary['success_count']}",
        f"- failed_count: {summary['failed_count']}",
        f"- render_failed_count: {summary['render_failed_count']}",
        f"- skipped_render_count: {skipped_render_count}",
        "",
        "| index | slug | topic | status | json_path | png_path | audio_path | wav_path | mp4_path | error |",
        "|---|---|---|---|---|---|---|---|---|---|",
    ]
    for item in summary["items"]:
        row = [
            str(item.get("index", "")),
            str(item.get("slug", "")),
            str(item.get("topic", "")),
            str(item.get("status", "")),
            str(item.get("json_path", "")),
            str(item.get("png_path", "")),
            str(item.get("audio_path", "")),
            str(item.get("wav_path", "")),
            str(item.get("mp4_path", "")),
            str(item.get("error", "")).replace("\n", " "),
        ]
        lines.append(f"| {' | '.join(row)} |")
    report_path.write_text("\n".join(lines) + "\n", encoding="utf-8")


def run_batch(payload: dict[str, Any], output_dir: Path) -> dict[str, Any]:
    items = payload.get("items")
    if not isinstance(items, list) or not items:
        raise ValueError("items must be a non-empty list")
    defaults = _build_defaults(payload)
    output_dir.mkdir(parents=True, exist_ok=True)
    events_path = output_dir / "events.jsonl"
    if events_path.exists():
        events_path.unlink()
    _write_event(events_path, {"event": "batch_started", "output_dir": str(output_dir), "total_items": len(items)})

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
            _write_event(events_path, {"event": "item_started", "index": idx, "slug": slug})

            generate_background = _ensure_bool(merged.get("generate_background", False), f"items[{idx}].generate_background")
            generate_voiceover_placeholder = _ensure_bool(
                merged.get("generate_voiceover_placeholder", False), f"items[{idx}].generate_voiceover_placeholder"
            )
            render_mp4 = _ensure_bool(merged.get("render_mp4", False), f"items[{idx}].render_mp4")
            entry["render_requested"] = render_mp4
            duration_seconds = _int_or_raise(merged.get("duration_seconds"), f"items[{idx}].duration_seconds")
            scene_count = _int_or_raise(merged.get("scene_count"), f"items[{idx}].scene_count")
            _validate_timing(duration_seconds, scene_count, f"items[{idx}]")
            brand = str(merged.get("brand"))
            visual_style = merged.get("visual_style")

            item_dir = output_dir / slug
            item_dir.mkdir(parents=True, exist_ok=True)
            json_path = item_dir / f"{slug}.json"
            png_path = item_dir / f"{slug}.png"
            wav_path = item_dir / f"{slug}.wav"
            mp4_path = item_dir / f"{slug}.mp4"
            voiceover_provider = str(merged.get("voiceover_provider", "silent"))
            voiceover_format = _normalize_voiceover_format(merged.get("voiceover_format"), field_name=f"items[{idx}].voiceover_format")
            final_audio_format = voiceover_format or "wav"
            if voiceover_provider == "silent" and final_audio_format != "wav":
                raise ValueError(f"items[{idx}].voiceover_format must be wav when voiceover_provider is silent")
            voice_output_path = item_dir / f"{slug}.{final_audio_format}"

            voiceover_audio_path = str(voice_output_path) if generate_voiceover_placeholder else None
            background_image_path = str(png_path) if generate_background else None

            resolved_style = resolve_visual_style(brand, visual_style)
            if generate_background:
                generate_background_png(style=resolved_style, brand=brand, output=png_path)
                entry["png_path"] = str(png_path)
                _write_event(events_path, {"event": "background_written", "index": idx, "slug": slug, "path": str(png_path)})
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
            scene_images = generate_scene_images(storyboard, item_dir)
            if scene_images:
                for scene_idx, scene in enumerate(storyboard.get("scenes", [])):
                    if scene_idx < len(scene_images) and isinstance(scene, dict):
                        scene["image_path"] = scene_images[scene_idx]
                if isinstance(storyboard.get("background"), dict) and scene_images:
                    storyboard["background"]["type"] = "image"
                    storyboard["background"]["path"] = scene_images[0]
                entry["scene_images"] = scene_images
            json_path.write_text(json.dumps(storyboard, indent=2), encoding="utf-8")
            _write_event(events_path, {"event": "storyboard_written", "index": idx, "slug": slug, "path": str(json_path)})
            entry["slug"] = slug
            entry["topic"] = topic
            entry["json_path"] = str(json_path)

            if generate_voiceover_placeholder:
                cfg = load_reel_config(json_path)
                voiceover_voice = merged.get("voiceover_voice")
                provider = get_provider(voiceover_provider)
                provider.generate(config=cfg, output=voice_output_path, voice=voiceover_voice, audio_format=final_audio_format)
                entry["audio_path"] = str(voice_output_path)
                if voice_output_path.suffix.lower() == ".wav":
                    entry["wav_path"] = str(voice_output_path)
                _write_event(events_path, {"event": "voiceover_written", "index": idx, "slug": slug, "path": str(voice_output_path), "provider": voiceover_provider})

            if render_mp4:
                try:
                    render_reel(load_reel_config(json_path), mp4_path)
                    entry["mp4_path"] = str(mp4_path)
                    _write_event(events_path, {"event": "render_written", "index": idx, "slug": slug, "path": str(mp4_path)})
                except RuntimeError as exc:
                    entry["status"] = "render_failed"
                    entry["error"] = str(exc)
            _write_event(events_path, {"event": "item_completed", "index": idx, "slug": slug, "status": entry["status"]})
            summary_items.append(entry)
        except Exception as exc:
            entry.setdefault("slug", _slugify(str(raw_item.get("slug", ""))) if isinstance(raw_item, dict) else "")
            if isinstance(raw_item, dict):
                topic = str(raw_item.get("topic", "")).strip()
                if topic:
                    entry["topic"] = topic
            entry["status"] = "failed"
            entry["error"] = str(exc)
            _write_event(
                events_path,
                {"event": "item_failed", "index": idx, "slug": entry.get("slug", ""), "error": str(exc), "status": entry["status"]},
            )
            summary_items.append(entry)

    summary = _build_summary(output_dir, summary_items)
    (output_dir / "summary.json").write_text(json.dumps(summary, indent=2), encoding="utf-8")
    _write_run_report(summary, output_dir / "run_report.md")
    _write_event(events_path, {"event": "batch_completed", "output_dir": str(output_dir)})
    return summary


def _print_summary(summary: dict[str, Any]) -> None:
    for item in summary["items"]:
        slug = item.get("slug") or f"index_{item.get('index')}"
        parts = [f"slug={slug}", f"status={item.get('status')}"]
        for key in ("json_path", "png_path", "audio_path", "wav_path", "mp4_path"):
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
