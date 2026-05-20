from __future__ import annotations
import argparse, json, time
from pathlib import Path
import requests
from reels.publish_config import load_publish_config
from reels.publish_urls import build_public_output_url
from reels.publish_facebook_reels import post_facebook_reel

def _load_json(path):
    with open(path, "r", encoding="utf-8") as f: return json.load(f)

def _build_caption(payload):
    # Use scene text for caption, not voiceover script (voiceover has pause markers)
    v = payload.get("voiceover") if isinstance(payload, dict) else None
    script = v.get("script") if isinstance(v, dict) else ""
    if isinstance(script, str) and script.strip(): return script.strip().replace("(pause)", "").replace("  ", " ").strip()[:2000]
    title = str(payload.get("title","")).strip()
    scenes = payload.get("scenes") if isinstance(payload, dict) else None
    scene_text = ""
    if isinstance(scenes, list) and scenes:
        first = scenes[0] if isinstance(scenes[0], dict) else {}
        scene_text = str(first.get("text") or "").strip()
    return "\n".join([x for x in [title, scene_text] if x])[:2000]

def _graph_url(version, edge):
    return f"https://graph.facebook.com/{version}/{edge}"

def _publish_instagram(video_url, caption, cfg):
    r = requests.post(_graph_url(cfg.meta_graph_version, f"{cfg.ig_business_id}/media"),
        data={"media_type":"REELS","video_url":video_url,"caption":caption,"access_token":cfg.meta_access_token},
        timeout=30)
    data = r.json()
    creation_id = data.get("id")
    if not creation_id: return {"status":"failed","error":"missing_creation_id","response":data}
    deadline = time.time() + 180
    readiness = None
    while time.time() < deadline:
        sr = requests.get(_graph_url(cfg.meta_graph_version, str(creation_id)),
            params={"fields":"status_code,status","access_token":cfg.meta_access_token}, timeout=30)
        readiness = sr.json()
        sc = str(readiness.get("status_code","")).upper()
        if sc == "FINISHED": break
        if sc in {"ERROR","EXPIRED"}: return {"status":"failed","creation_id":creation_id,"readiness":readiness}
        time.sleep(3)
    else:
        return {"status":"failed","creation_id":creation_id,"error":"timeout","readiness":readiness}
    pub = requests.post(_graph_url(cfg.meta_graph_version, f"{cfg.ig_business_id}/media_publish"),
        data={"creation_id":creation_id,"access_token":cfg.meta_access_token}, timeout=30)
    pd = pub.json()
    if "id" not in pd: return {"status":"failed","creation_id":creation_id,"publish":pd}
    return {"status":"success","creation_id":creation_id,"publish":pd}

def publish_reel(input_path, video_path, platform, dry_run, public_base_url=None, logger=None):
    cfg = load_publish_config()
    video_file = Path(video_path)
    if not video_file.exists(): raise FileNotFoundError(f"video not found: {video_file}")
    payload = _load_json(Path(input_path))
    caption = _build_caption(payload)
    public_base = (public_base_url or cfg.public_base_url).strip()
    effective_dry_run = dry_run or cfg.post_dry_run
    video_url = ""
    if public_base and platform in {"instagram","both"}:
        try: video_url = build_public_output_url(public_base, video_file)
        except Exception: pass
    result = {"dry_run":effective_dry_run,"platform":platform,"video_url":video_url,"caption":caption,"instagram":None,"facebook":None}
    do_ig = platform in {"instagram","both"}
    do_fb = platform in {"facebook","both"}
    if effective_dry_run:
        if do_ig: result["instagram"] = {"status":"planned","video_url":video_url}
        if do_fb: result["facebook"] = {"status":"planned","method":"binary_upload_reels_endpoint"}
        print(json.dumps(result, indent=2)); return result
    if do_ig:
        if not video_url: result["instagram"] = {"status":"failed","error":"REELS_PUBLIC_BASE_URL not set"}
        else: result["instagram"] = _publish_instagram(video_url, caption, cfg)
    if do_fb:
        result["facebook"] = post_facebook_reel(video_path=video_file, caption=caption,
            access_token=cfg.meta_access_token, page_id=cfg.fb_page_id,
            graph_version=cfg.meta_graph_version, logger=logger)
    print(json.dumps(result, indent=2)); return result

def main():
    p = argparse.ArgumentParser()
    p.add_argument("--input", required=True)
    p.add_argument("--video", required=True)
    p.add_argument("--platform", choices=["instagram","facebook","both"], default="both")
    p.add_argument("--dry-run", action="store_true")
    p.add_argument("--public-base-url", default=None)
    a = p.parse_args()
    publish_reel(a.input, a.video, a.platform, a.dry_run, a.public_base_url)
    return 0

if __name__ == "__main__": raise SystemExit(main())
