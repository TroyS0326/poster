from __future__ import annotations
import os, time
from pathlib import Path
import requests

def _mask(token):
    if not token or len(token) < 8: return "***"
    return f"{token[:4]}...{token[-4:]}"

def _safe_json(resp):
    try: return resp.json()
    except: return {"raw": resp.text[:500]}

def post_facebook_reel(video_path, caption, access_token, page_id, graph_version="v20.0", logger=None):
    def log(msg, *args, level="info"):
        if logger: getattr(logger, level, logger.info)(msg, *args)
        else: print(f"[{level.upper()}] {msg % args if args else msg}")

    video_file = Path(video_path).resolve()
    if not video_file.exists():
        raise FileNotFoundError(f"Video not found: {video_file}")
    if video_file.suffix.lower() != ".mp4":
        raise ValueError(f"Facebook Reels requires .mp4, got: {video_file.suffix}")

    file_size = video_file.stat().st_size
    api_base = f"https://graph.facebook.com/{graph_version}"
    log("fb_reel upload start: file=%s size=%d", video_file.name, file_size)

    try:
        init = requests.post(f"{api_base}/{page_id}/video_reels",
            data={"upload_phase": "start", "access_token": access_token}, timeout=30)
    except requests.RequestException as e:
        return {"status": "failed", "phase": "init", "error": str(e)}

    init_data = _safe_json(init)
    if not init.ok:
        return {"status": "failed", "phase": "init", "status_code": init.status_code, "response": init_data}

    video_id = init_data.get("video_id")
    upload_url = init_data.get("upload_url")
    if not video_id or not upload_url:
        return {"status": "failed", "phase": "init", "error": "missing video_id or upload_url", "response": init_data}

    log("fb_reel init ok: video_id=%s", video_id)

    try:
        with open(video_file, "rb") as fh:
            up = requests.post(upload_url,
                headers={"Authorization": f"OAuth {access_token}", "offset": "0", "file_size": str(file_size)},
                data=fh, timeout=600)
    except requests.RequestException as e:
        return {"status": "failed", "phase": "upload", "video_id": video_id, "error": str(e)}

    if not up.ok:
        return {"status": "failed", "phase": "upload", "video_id": video_id, "status_code": up.status_code}

    log("fb_reel upload complete: video_id=%s", video_id)
    time.sleep(2)

    try:
        pub = requests.post(f"{api_base}/{page_id}/video_reels",
            data={"upload_phase": "finish", "video_id": video_id, "video_state": "PUBLISHED",
                  "description": caption[:2000], "access_token": access_token}, timeout=60)
    except requests.RequestException as e:
        return {"status": "failed", "phase": "publish", "video_id": video_id, "error": str(e)}

    pub_data = _safe_json(pub)
    if pub_data.get("success") is True or pub_data.get("id") or pub_data.get("post_id"):
        log("fb_reel published ok: video_id=%s", video_id)
        return {"status": "success", "video_id": video_id, "response": pub_data}

    log("fb_reel publish failed: %s", pub_data, level="error")
    return {"status": "failed", "phase": "publish", "video_id": video_id, "response": pub_data}
