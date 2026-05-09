import random
import time
from quality import validate_caption, validate_image_prompt
from text_ai import generate_content_package
from image_ai import generate_image
from uploader import upload_image
from meta_poster import post_to_meta


def _package_fields(package: dict) -> tuple[str | None, str | None, str]:
    if not isinstance(package, dict):
        return None, None, ""
    return package.get("caption"), package.get("image_prompt"), package.get("negative_prompt", "")


def run_workflow(config, logger):
    logger.info("workflow started")
    package = None

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

    caption, image_prompt, negative_prompt = _package_fields(package)
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
