import requests


def _graph_url(version: str, path: str) -> str:
    return f"https://graph.facebook.com/{version}/{path.lstrip('/')}"


def _safe_post(url: str, data: dict, logger):
    try:
        response = requests.post(url, data=data, timeout=45)
    except requests.RequestException as exc:
        logger.warning("meta request failed for %s: %s", url, exc)
        return None, {"status": "failed", "response": {"error": str(exc)}, "status_code": None}

    try:
        body = response.json()
    except ValueError as exc:
        logger.warning("meta non-json response for %s: %s", url, exc)
        body = response.text

    if not response.ok:
        logger.warning("meta request failed for %s with status %s: %s", url, response.status_code, body)
        return response, {"status": "failed", "response": body, "status_code": response.status_code}

    if isinstance(body, dict) and body.get("error"):
        logger.warning("meta request returned error for %s: %s", url, body.get("error"))
        return response, {"status": "failed", "response": body, "status_code": response.status_code}
    return response, {"status": "success", "response": body, "status_code": response.status_code}


def post_to_meta(caption: str, image_url: str, config, logger):
    if config.dry_run:
        logger.info("DRY_RUN enabled: would post caption and image_url=%s", image_url)
        return {
            "dry_run": True,
            "facebook": {"status": "skipped", "reason": "dry_run"},
            "instagram": {"status": "skipped", "reason": "dry_run"},
        }

    token = config.meta_access_token

    _, fb_result = _safe_post(
        _graph_url(config.meta_graph_version, f"{config.fb_page_id}/photos"),
        {"caption": caption, "url": image_url, "access_token": token},
        logger,
    )

    _, media_result = _safe_post(
        _graph_url(config.meta_graph_version, f"{config.ig_business_id}/media"),
        {"image_url": image_url, "caption": caption, "access_token": token},
        logger,
    )

    if media_result["status"] == "success" and media_result.get("response", {}).get("id"):
        _, publish_result = _safe_post(
            _graph_url(config.meta_graph_version, f"{config.ig_business_id}/media_publish"),
            {"creation_id": media_result["response"]["id"], "access_token": token},
            logger,
        )
        ig_result = {
            "status": "success" if publish_result["status"] == "success" else "failed",
            "container": media_result,
            "publish": publish_result,
        }
    else:
        ig_result = {
            "status": "failed",
            "container": media_result,
            "publish": {"status": "skipped", "reason": "container_failed"},
        }

    return {"dry_run": False, "facebook": fb_result, "instagram": ig_result}
