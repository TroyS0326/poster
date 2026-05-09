import argparse
import json
import time
from pathlib import Path

import requests

from reels.publish_config import load_publish_config
from reels.publish_urls import build_public_output_url


def _load_input_json(path: Path) -> dict:
    with path.open("r", encoding="utf-8") as fh:
        return json.load(fh)


def _build_caption(payload: dict) -> str:
    voiceover = payload.get("voiceover") if isinstance(payload, dict) else None
    script = voiceover.get("script") if isinstance(voiceover, dict) else ""
    if isinstance(script, str) and script.strip():
        return script.strip()[:2000]

    title = str(payload.get("title", "")).strip() if isinstance(payload, dict) else ""
    scene_text = ""
    scenes = payload.get("scenes") if isinstance(payload, dict) else None
    if isinstance(scenes, list) and scenes:
        first = scenes[0] if isinstance(scenes[0], dict) else {}
        scene_text = str(first.get("text") or "").strip()
    return "\n".join([x for x in [title, scene_text] if x])[:2000]


def _graph_url(version: str, edge: str, host: str = "graph.facebook.com") -> str:
    return f"https://{host}/{version}/{edge}"


def _publish_instagram(video_url: str, caption: str, cfg) -> dict:
    media_resp = requests.post(
        _graph_url(cfg.meta_graph_version, f"{cfg.ig_business_id}/media"),
        data={"media_type": "REELS", "video_url": video_url, "caption": caption, "access_token": cfg.meta_access_token},
        timeout=30,
    )
    media_data = media_resp.json()
    creation_id = media_data.get("id")
    if not creation_id:
        return {"status": "failed", "error": "missing_creation_id", "response": media_data}

    deadline = time.time() + 180
    readiness = None
    while time.time() < deadline:
        status_resp = requests.get(
            _graph_url(cfg.meta_graph_version, str(creation_id)),
            params={"fields": "status_code,status", "access_token": cfg.meta_access_token},
            timeout=30,
        )
        readiness = status_resp.json()
        status_code = str(readiness.get("status_code", "")).upper()
        if status_code == "FINISHED":
            break
        if status_code in {"ERROR", "EXPIRED"}:
            return {"status": "failed", "creation_id": creation_id, "readiness": readiness}
        time.sleep(2)
    else:
        return {"status": "failed", "creation_id": creation_id, "error": "timeout", "readiness": readiness}

    pub_resp = requests.post(
        _graph_url(cfg.meta_graph_version, f"{cfg.ig_business_id}/media_publish"),
        data={"creation_id": creation_id, "access_token": cfg.meta_access_token},
        timeout=30,
    )
    pub_data = pub_resp.json()
    if "id" not in pub_data:
        return {"status": "failed", "creation_id": creation_id, "publish": pub_data}
    return {"status": "success", "creation_id": creation_id, "publish": pub_data}


def _publish_facebook(video_url: str, caption: str, cfg) -> dict:
    resp = requests.post(
        _graph_url(cfg.meta_graph_version, f"{cfg.fb_page_id}/videos", host="graph-video.facebook.com"),
        data={"file_url": video_url, "description": caption, "access_token": cfg.meta_access_token},
        timeout=60,
    )
    data = resp.json()
    if "id" not in data and not data.get("success"):
        return {"status": "failed", "response": data}
    return {"status": "success", "response": data}


def publish_reel(input_path: str, video_path: str, platform: str, dry_run: bool, public_base_url: str | None = None) -> dict:
    cfg = load_publish_config()
    input_file = Path(input_path)
    video_file = Path(video_path)
    if not video_file.exists():
        raise FileNotFoundError(f"video file does not exist: {video_file}")

    payload = _load_input_json(input_file)
    caption = _build_caption(payload)
    public_base = (public_base_url or cfg.public_base_url).strip()
    if not public_base:
        raise ValueError("Missing public base URL. Set --public-base-url or REELS_PUBLIC_BASE_URL")

    video_url = build_public_output_url(public_base, video_file)
    effective_dry_run = dry_run or cfg.post_dry_run

    result = {
        "dry_run": effective_dry_run,
        "platform": platform,
        "video_url": video_url,
        "caption": caption,
        "instagram": None,
        "facebook": None,
    }
    do_ig = platform in {"instagram", "both"}
    do_fb = platform in {"facebook", "both"}

    if effective_dry_run:
        if do_ig:
            result["instagram"] = {"status": "planned"}
        if do_fb:
            result["facebook"] = {"status": "planned"}
        print(json.dumps(result, indent=2))
        return result

    if do_ig:
        result["instagram"] = _publish_instagram(video_url, caption, cfg)
    if do_fb:
        result["facebook"] = _publish_facebook(video_url, caption, cfg)

    print(json.dumps(result, indent=2))
    return result


def main() -> int:
    parser = argparse.ArgumentParser(description="Publish generated reels assets")
    parser.add_argument("--input", required=True)
    parser.add_argument("--video", required=True)
    parser.add_argument("--platform", choices=["instagram", "facebook", "both"], default="instagram")
    parser.add_argument("--dry-run", action="store_true")
    parser.add_argument("--public-base-url", default=None)
    args = parser.parse_args()

    publish_reel(args.input, args.video, args.platform, args.dry_run, args.public_base_url)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
