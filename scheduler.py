import hashlib
import json
import os
import random
import time
from quality import validate_caption, validate_image_prompt
from prompts import build_caption, needs_risk_disclosure, should_include_url
from text_ai import generate_content_package
from image_ai import generate_image
from uploader import upload_image
from meta_poster import post_to_meta
from meta_preflight import run_preflight


def _package_fields(package: dict) -> tuple[str | None, str | None, str]:
    if not isinstance(package, dict):
        return None, None, ""
    return package.get("caption"), package.get("image_prompt"), package.get("negative_prompt", "")


def _caption_history_path(config):
    log_path = getattr(config, "log_path", "logs/xeanvi_social_bot.log")
    return os.path.join(os.path.dirname(log_path) or ".", "caption_history.json")


def _load_caption_history(config, logger):
    path = _caption_history_path(config)
    try:
        with open(path, "r", encoding="utf-8") as f:
            data = json.load(f)
        if isinstance(data, list):
            return path, [str(x) for x in data][-50:]
    except FileNotFoundError:
        return path, []
    except Exception as exc:
        logger.warning("caption history load failed: %s", exc)
    return path, []


def _save_caption_history(path, hashes, logger):
    try:
        os.makedirs(os.path.dirname(path) or ".", exist_ok=True)
        with open(path, "w", encoding="utf-8") as f:
            json.dump(hashes[-50:], f)
    except Exception as exc:
        logger.warning("caption history save failed: %s", exc)


def _caption_hash(caption):
    return hashlib.sha256((caption or "").encode("utf-8")).hexdigest()


def run_workflow(config, logger):
    logger.info("workflow started")
    package = None
    history_path, caption_history = _load_caption_history(config, logger)

    for attempt in range(1, config.max_generation_attempts + 1):
        try:
            candidate = generate_content_package(config, logger)
            caption, image_prompt, _ = _package_fields(candidate)
            if not caption or not image_prompt:
                logger.warning("malformed content package on attempt %s", attempt)
                if attempt == config.max_generation_attempts:
                    logger.error("malformed content after %s attempts, skipping post", attempt)
                    return
                continue

            logger.info("caption generated")
            pillar = candidate.get("pillar", "")
            archetype = candidate.get("archetype", "")
            needs_disclosure = needs_risk_disclosure(f"{pillar} {archetype} {caption}")
            include_url = should_include_url(pillar, archetype)
            seed_blob = f"{time.time_ns()}|{random.randint(0, 10**9)}|{pillar}|{archetype}|{attempt}"
            for variation_attempt in range(1, 6):
                seed = f"{seed_blob}|{variation_attempt}"
                candidate["caption"] = build_caption(pillar, archetype, include_url, needs_disclosure, seed=seed)
                caption = candidate["caption"]
                caption_sig = _caption_hash(caption)
                if caption_sig not in caption_history:
                    break
                logger.info("duplicate caption hash detected; regenerating (attempt %s)", variation_attempt)
            else:
                logger.warning("all caption variants duplicated recent history; using latest generated variant")
            cap_ok, cap_reason = validate_caption(caption)
            prm_ok, prm_reason = validate_image_prompt(image_prompt)
            logger.info("caption quality %s (%s)", "passed" if cap_ok else "failed", cap_reason)
            logger.info("image prompt quality %s (%s)", "passed" if prm_ok else "failed", prm_reason)
            if cap_ok and prm_ok:
                package = candidate
                break
        except Exception as exc:
            logger.exception("workflow attempt %s failed: %s", attempt, exc)

        if attempt == config.max_generation_attempts:
            logger.error("quality/workflow failed after %s attempts, skipping post", attempt)
            return

    if not config.dry_run and not config.manual_review_mode:
        preflight = run_preflight()
        if preflight["fb_page_id"] != "valid" or preflight["ig_business_id"] != "valid":
            logger.error("meta preflight failed: %s", preflight)
            return

    caption, image_prompt, negative_prompt = _package_fields(package)
    caption_sig = _caption_hash(caption)
    caption_history = (caption_history + [caption_sig])[-50:]
    _save_caption_history(history_path, caption_history, logger)
    logger.info("image prompt generated")
    image_result = generate_image(config, image_prompt, negative_prompt, logger)
    if not image_result:
        logger.error("image generation failed, skipping post")
        return

    logger.info("image generated: %s", image_result["local_path"])
    if config.prefer_local_public_image_url:
        hosted_url = upload_image(image_result["local_path"], config)
        logger.info("using locally hosted public image URL")
    elif image_result.get("remote_url"):
        hosted_url = image_result["remote_url"]
        logger.info("using remote image URL from provider")
    else:
        hosted_url = upload_image(image_result["local_path"], config)
        logger.info("using locally hosted public image URL fallback")
    logger.info("hosted/public image URL created: %s", hosted_url)

    if config.manual_review_mode:
        logger.info("MANUAL_REVIEW_MODE enabled; package=%s image_url=%s", package, hosted_url)
        result = {
            "dry_run": config.dry_run,
            "facebook": {"status": "skipped", "reason": "manual_review_mode"},
            "instagram": {"status": "skipped", "reason": "manual_review_mode"},
        }
    else:
        result = post_to_meta(caption, hosted_url, config, logger)

    logger.info("Facebook posted or failed: %s", result["facebook"]["status"])
    logger.info("Instagram container created/published or failed: %s", result["instagram"]["status"])


def schedule_posts(config, logger):
    interval = max(1, config.post_interval_hours)
    logger.info("scheduler started; posting every %s hour(s)", interval)
    while True:
        try:
            run_workflow(config, logger)
        except Exception as exc:
            logger.exception("unexpected scheduler workflow failure: %s", exc)
        jitter = random.randint(0, max(0, config.randomize_interval_minutes))
        sleep_seconds = (interval * 3600) + (jitter * 60)
        logger.info("sleep time: %s seconds", sleep_seconds)
        time.sleep(sleep_seconds)
