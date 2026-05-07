import requests


def _graph_url(version: str, path: str) -> str:
    return f"https://graph.facebook.com/{version}/{path.lstrip('/')}"


def post_to_meta(caption: str, image_url: str, config, logger):
    if config.dry_run:
        logger.info("DRY_RUN enabled: would post caption and image_url=%s", image_url)
        return {"dry_run": True, "facebook": {"status": "skipped"}, "instagram": {"status": "skipped"}}

    token = config.meta_access_token
    fb_result = {"status": "failed"}
    ig_result = {"status": "failed"}

    fb_resp = requests.post(
        _graph_url(config.meta_graph_version, f"{config.fb_page_id}/photos"),
        data={"caption": caption, "url": image_url, "access_token": token}, timeout=45,
    )
    fb_json = fb_resp.json()
    fb_result = {"status": "success" if fb_resp.ok and not fb_json.get("error") else "failed", "response": fb_json}

    media_resp = requests.post(
        _graph_url(config.meta_graph_version, f"{config.ig_business_id}/media"),
        data={"image_url": image_url, "caption": caption, "access_token": token}, timeout=45,
    )
    media_json = media_resp.json()
    if media_resp.ok and not media_json.get("error") and media_json.get("id"):
        publish_resp = requests.post(
            _graph_url(config.meta_graph_version, f"{config.ig_business_id}/media_publish"),
            data={"creation_id": media_json["id"], "access_token": token}, timeout=45,
        )
        publish_json = publish_resp.json()
        ig_result = {"status": "success" if publish_resp.ok and not publish_json.get("error") else "failed", "container": media_json, "publish": publish_json}
    else:
        ig_result = {"status": "failed", "container": media_json, "publish": {"skipped": True}}

    return {"dry_run": False, "facebook": fb_result, "instagram": ig_result}
