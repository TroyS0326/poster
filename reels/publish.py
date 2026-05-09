import argparse
import json
from pathlib import Path

import requests

from config import load_config
from meta_poster import _graph_url, _safe_post, _wait_for_ig_container_ready
from reels.publish_config import load_publish_config
from reels.publish_urls import build_public_output_url


class _PrintLogger:
    def info(self, msg, *args):
        print(msg % args if args else msg)

    warning = info
    error = info


def _load_input_json(path: Path) -> dict:
    with path.open("r", encoding="utf-8") as fh:
        return json.load(fh)


def _build_caption(payload: dict) -> str:
    voiceover = payload.get("voiceover") if isinstance(payload, dict) else None
    script = voiceover.get("script") if isinstance(voiceover, dict) else ""
    if isinstance(script, str) and script.strip():
        return script.strip()

    title = str(payload.get("title", "")).strip() if isinstance(payload, dict) else ""
    scene_text = ""
    scenes = payload.get("scenes") if isinstance(payload, dict) else None
    if isinstance(scenes, list) and scenes:
        first = scenes[0] if isinstance(scenes[0], dict) else {}
        texts = first.get("texts")
        if isinstance(texts, list):
            scene_text = " ".join(str(x).strip() for x in texts if str(x).strip())

    caption = "\n".join([part for part in [title, scene_text] if part]).strip()
    return caption[:2000]


def publish_reel(input_path: str, video_path: str, platform: str, dry_run: bool, public_base_url: str | None = None) -> dict:
    cfg = load_config()
    pub_cfg = load_publish_config()
    logger = _PrintLogger()

    input_file = Path(input_path)
    video_file = Path(video_path)
    if not video_file.exists():
        raise FileNotFoundError(f"video file does not exist: {video_file}")

    payload = _load_input_json(input_file)
    caption = _build_caption(payload)
    public_base = (public_base_url or pub_cfg.public_base_url).strip()
    if not public_base:
        raise ValueError("Missing public base URL. Set --public-base-url or REELS_PUBLIC_BASE_URL")

    video_url = build_public_output_url(public_base, video_file)
    effective_dry_run = dry_run or pub_cfg.post_dry_run

    if effective_dry_run:
        result = {
            "dry_run": True,
            "platform": platform,
            "video_url": video_url,
            "caption": caption,
        }
        print(json.dumps(result, indent=2))
        return result

    if platform != "instagram":
        raise ValueError(f"unsupported platform for non-dry-run: {platform}")

    token = cfg.meta_access_token
    _, media_result = _safe_post(
        _graph_url(cfg.meta_graph_version, f"{cfg.ig_business_id}/media"),
        {
            "media_type": "REELS",
            "video_url": video_url,
            "caption": caption,
            "access_token": token,
        },
        logger,
    )

    if media_result.get("status") != "success" or not media_result.get("response", {}).get("id"):
        print(json.dumps({"status": "failed", "container": media_result}, indent=2))
        return {"status": "failed", "container": media_result}

    creation_id = media_result["response"]["id"]
    readiness = _wait_for_ig_container_ready(creation_id, cfg, token, logger)
    if not readiness.get("ready"):
        result = {"status": "failed", "container": media_result, "readiness": readiness}
        print(json.dumps(result, indent=2))
        return result

    _, publish_result = _safe_post(
        _graph_url(cfg.meta_graph_version, f"{cfg.ig_business_id}/media_publish"),
        {"creation_id": creation_id, "access_token": token},
        logger,
    )
    result = {"status": publish_result.get("status"), "container": media_result, "publish": publish_result}
    print(json.dumps(result, indent=2))
    return result


def main() -> int:
    parser = argparse.ArgumentParser(description="Publish generated reels assets")
    parser.add_argument("--input", required=True)
    parser.add_argument("--video", required=True)
    parser.add_argument("--platform", choices=["instagram", "facebook"], default="instagram")
    parser.add_argument("--dry-run", action="store_true")
    parser.add_argument("--public-base-url", default=None)
    args = parser.parse_args()

    if args.platform == "facebook" and not args.dry_run:
        raise SystemExit("facebook publishing is not implemented yet; use --dry-run")

    publish_reel(
        input_path=args.input,
        video_path=args.video,
        platform=args.platform,
        dry_run=args.dry_run,
        public_base_url=args.public_base_url,
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
