import requests
import time


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


def _wait_for_ig_container_ready(creation_id: str, config, token: str, logger):
    url = _graph_url(config.meta_graph_version, creation_id)
    params = {"fields": "status_code,status", "access_token": token}

    for attempt in range(1, 11):
        try:
            response = requests.get(url, params=params, timeout=45)
        except requests.RequestException as exc:
            logger.warning("instagram media container status check failed for %s: %s", creation_id, exc)
            return {
                "ready": False,
                "response": {"error": str(exc)},
                "reason": "request_failed",
            }

        try:
            body = response.json()
        except ValueError:
            body = {"raw": response.text}

        status_code = body.get("status_code") if isinstance(body, dict) else None
        logger.info("instagram media container status attempt %s: %s", attempt, status_code)

        if not response.ok:
            logger.warning(
                "instagram media container status request failed for %s with status %s",
                creation_id,
                response.status_code,
            )
            return {"ready": False, "response": body, "reason": "request_failed"}

        if status_code == "FINISHED":
            return {"ready": True, "response": body}
        if status_code in {"ERROR", "EXPIRED"}:
            return {"ready": False, "response": body, "reason": "failed_status"}

        if attempt < 10:
            time.sleep(3)

    return {"ready": False, "response": body, "reason": "timeout"}


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
        creation_id = media_result["response"]["id"]
        readiness_result = _wait_for_ig_container_ready(creation_id, config, token, logger)

        if not readiness_result["ready"]:
            ig_result = {
                "status": "failed",
                "container": media_result,
                "readiness": readiness_result,
                "publish": {"status": "skipped", "reason": "container_not_ready"},
            }
            return {"dry_run": False, "facebook": fb_result, "instagram": ig_result}

        _, publish_result = _safe_post(
            _graph_url(config.meta_graph_version, f"{config.ig_business_id}/media_publish"),
            {"creation_id": creation_id, "access_token": token},
            logger,
        )

        publish_error = publish_result.get("response", {}).get("error", {}) if isinstance(publish_result.get("response"), dict) else {}
        if (
            publish_result["status"] == "failed"
            and publish_error.get("code") == 9007
            and publish_error.get("error_subcode") == 2207027
        ):
            logger.info("instagram media_publish not ready yet for %s, retrying once", creation_id)
            time.sleep(5)
            _, publish_result = _safe_post(
                _graph_url(config.meta_graph_version, f"{config.ig_business_id}/media_publish"),
                {"creation_id": creation_id, "access_token": token},
                logger,
            )

        ig_result = {
            "status": "success" if publish_result["status"] == "success" else "failed",
            "container": media_result,
            "readiness": readiness_result,
            "publish": publish_result,
        }
    else:
        ig_result = {
            "status": "failed",
            "container": media_result,
            "publish": {"status": "skipped", "reason": "container_failed"},
        }

    return {"dry_run": False, "facebook": fb_result, "instagram": ig_result}
