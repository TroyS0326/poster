from __future__ import annotations

import argparse
import json
from pathlib import Path

from reels.batch import run_batch
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


def run_autopost(queue_file: Path, run_id: str, public_base_url: str, limit: int = 3, dry_run: bool = False) -> dict:
    payload = load_queue_input(queue_file)
    runs = validate_queue_payload(payload)
    run = _select_run(runs, run_id)
    output_root = _resolve_output_root(payload)
    run_dir = output_root / run_id
    summary_path = run_dir / "summary.json"
    if not summary_path.exists():
        run_batch(_build_batch_payload(payload, run), run_dir)

    summary = json.loads(summary_path.read_text(encoding="utf-8"))
    cfg = load_publish_config()

    events_path = run_dir / "publish_events.jsonl"
    out_summary_path = run_dir / "publish_summary.json"
    events: list[dict] = []
    items = []

    for item in summary.get("items", [])[:limit]:
        item_result = {"slug": item.get("slug"), "json_path": item.get("json_path"), "mp4_path": item.get("mp4_path")}
        publish_result = publish_reel(
            input_path=item["json_path"],
            video_path=item["mp4_path"],
            platform="both",
            dry_run=dry_run,
            public_base_url=public_base_url,
        )
        item_result["publish"] = publish_result
        ig_ok = publish_result.get("instagram", {}).get("status") == "success"
        fb_ok = publish_result.get("facebook", {}).get("status") == "success"
        item_result["cleanup"] = {"deleted": []}
        if dry_run:
            print(f"planned_publish slug={item.get('slug')} url={publish_result.get('video_url')}")
        elif ig_ok and fb_ok and cfg.cleanup_after_success:
            item_dir = Path(item["json_path"]).parent
            item_result["cleanup"]["deleted"] = _delete_heavy_files(item_dir, cfg.delete_after_success_extensions)
        items.append(item_result)
        events.append({"slug": item.get("slug"), "dry_run": dry_run, "instagram": publish_result.get("instagram"), "facebook": publish_result.get("facebook")})

    result = {"run_id": run_id, "dry_run": dry_run, "limit": limit, "processed": len(items), "items": items}
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
    args = parser.parse_args()

    run_autopost(Path(args.queue), args.run_id, args.public_base_url, limit=args.limit, dry_run=args.dry_run)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
