from __future__ import annotations

import argparse
import json
from pathlib import Path

from reels.batch import run_batch
import os

from reels.generate import load_reel_config, render_reel
from reels.video_assets import load_video_manifest
from reels.video_renderer import render_video_reel
from reels.publish import publish_reel
from reels.publish_config import load_publish_config
from reels.queue import _build_batch_payload, _resolve_output_root, _select_run, load_queue_input, validate_queue_payload


def _delete_heavy_files(item_dir: Path, allowed_exts: tuple[str, ...]) -> list[str]:
    deleted = []
    for p in item_dir.glob("*"):
        if p.is_file() and p.suffix.lower() in allowed_exts:
            p.unlink()
            deleted.append(str(p))
    return deleted


def _selected_platform(cfg, platform_override: str | None) -> str:
    if platform_override:
        return platform_override
    if cfg.post_to_instagram and cfg.post_to_facebook:
        return "both"
    if cfg.post_to_instagram:
        return "instagram"
    if cfg.post_to_facebook:
        return "facebook"
    return "none"


def _publish_success_for_platform(platform: str, publish_result: dict) -> bool:
    ig = publish_result.get("instagram") if isinstance(publish_result, dict) else None
    fb = publish_result.get("facebook") if isinstance(publish_result, dict) else None
    ig_ok = isinstance(ig, dict) and ig.get("status") == "success"
    fb_ok = isinstance(fb, dict) and fb.get("status") == "success"
    if platform == "both":
        return ig_ok and fb_ok
    if platform == "instagram":
        return ig_ok
    if platform == "facebook":
        return fb_ok
    return False


def _summary_has_missing_item_assets(summary: dict) -> bool:
    for item in summary.get("items", []):
        json_path = item.get("json_path")
        if not json_path or not Path(json_path).exists():
            return True
    return False


def run_autopost(
    queue_file: Path,
    run_id: str,
    public_base_url: str,
    limit: int = 3,
    dry_run: bool = False,
    platform_override: str | None = None,
) -> dict:
    payload = load_queue_input(queue_file)
    runs = validate_queue_payload(payload)
    run = _select_run(runs, run_id)
    output_root = _resolve_output_root(payload)
    run_dir = output_root / run_id
    summary_path = run_dir / "summary.json"
    if not summary_path.exists():
        run_batch(_build_batch_payload(payload, run), run_dir)

    summary = json.loads(summary_path.read_text(encoding="utf-8"))
    if _summary_has_missing_item_assets(summary):
        run_batch(_build_batch_payload(payload, run), run_dir)
        summary = json.loads(summary_path.read_text(encoding="utf-8"))

    cfg = load_publish_config()
    platform = _selected_platform(cfg, platform_override)
    effective_dry_run = dry_run or cfg.post_dry_run
    print(f"effective_dry_run={effective_dry_run}")

    if platform == "none" and not effective_dry_run:
        raise ValueError("No publish platform enabled. Set REELS_POST_TO_INSTAGRAM and/or REELS_POST_TO_FACEBOOK, or use dry-run.")

    events_path = run_dir / "publish_events.jsonl"
    out_summary_path = run_dir / "publish_summary.json"
    events: list[dict] = []
    items = []

    for item in summary.get("items", [])[:limit]:
        json_path = Path(item["json_path"])
        item_dir = json_path.parent
        slug = item["slug"]
        mp4_path = item.get("mp4_path") or str(item_dir / f"{slug}.mp4")

        item_result = {"slug": slug, "json_path": str(json_path), "mp4_path": str(mp4_path), "cleanup": {"deleted": []}}

        if not Path(mp4_path).exists():
            try:
                renderer = os.getenv("REELS_RENDERER", "video").strip().lower()
                cfg_obj = load_reel_config(json_path)
                if renderer == "legacy":
                    render_reel(cfg_obj, mp4_path)
                elif renderer == "video":
                    manifest = os.getenv("REELS_VIDEO_MANIFEST", "assets/reels/video_manifest.json")
                    clips = load_video_manifest(manifest)
                    render_video_reel(cfg_obj, mp4_path, clips=clips)
                else:
                    raise ValueError(f"Unknown REELS_RENDERER: {renderer}")
                events.append({"slug": slug, "event": "render_written", "mp4_path": str(mp4_path)})
            except Exception as exc:
                item_result["status"] = "render_failed"
                item_result["error"] = str(exc)
                events.append({"slug": slug, "event": "render_failed", "error": str(exc), "mp4_path": str(mp4_path)})
                items.append(item_result)
                continue

        if platform == "none":
            publish_result = {"dry_run": effective_dry_run, "platform": "none", "instagram": None, "facebook": None}
        else:
            publish_result = publish_reel(
                input_path=str(json_path),
                video_path=str(mp4_path),
                platform=platform,
                dry_run=effective_dry_run,
                public_base_url=public_base_url,
            )
        item_result["publish"] = publish_result

        if effective_dry_run:
            print(f"planned_publish slug={slug} url={publish_result.get('video_url')}")
        elif cfg.cleanup_after_success and _publish_success_for_platform(platform, publish_result):
            item_result["cleanup"]["deleted"] = _delete_heavy_files(item_dir, cfg.delete_after_success_extensions)

        items.append(item_result)
        events.append({
            "slug": slug,
            "event": "publish_completed",
            "dry_run": effective_dry_run,
            "platform": platform,
            "instagram": publish_result.get("instagram"),
            "facebook": publish_result.get("facebook"),
            "mp4_path": str(mp4_path),
        })

    result = {
        "run_id": run_id,
        "dry_run": effective_dry_run,
        "limit": limit,
        "platform": platform,
        "processed": len(items),
        "items": items,
    }
    with events_path.open("w", encoding="utf-8") as f:
        for e in events:
            f.write(json.dumps(e) + "\n")
    out_summary_path.write_text(json.dumps(result, indent=2), encoding="utf-8")
    print(json.dumps(result, indent=2))
    return result


def main() -> int:
    parser = argparse.ArgumentParser(description="Auto-publish reels queue runs")
    parser.add_argument("--queue", required=True)
    parser.add_argument("--run-id", required=True)
    parser.add_argument("--public-base-url", required=True)
    parser.add_argument("--limit", type=int, default=3)
    parser.add_argument("--dry-run", action="store_true")
    parser.add_argument("--platform", choices=["instagram", "facebook", "both"], default=None)
    args = parser.parse_args()

    run_autopost(
        Path(args.queue),
        args.run_id,
        args.public_base_url,
        limit=args.limit,
        dry_run=args.dry_run,
        platform_override=args.platform,
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
