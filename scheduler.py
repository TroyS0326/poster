import random
import time
from quality import validate_caption, validate_image_prompt
from text_ai import generate_content_package
from image_ai import generate_image
from uploader import upload_image
from meta_poster import post_to_meta


def run_workflow(config, logger):
    logger.info("workflow started")
    for attempt in range(1, config.max_generation_attempts + 1):
        package = generate_content_package(config, logger)
        logger.info("caption generated")
        cap_ok, cap_reason = validate_caption(package["caption"])
        prm_ok, prm_reason = validate_image_prompt(package["image_prompt"])
        logger.info("caption quality %s (%s)", "passed" if cap_ok else "failed", cap_reason)
        logger.info("image prompt quality %s (%s)", "passed" if prm_ok else "failed", prm_reason)
        if cap_ok and prm_ok:
            break
        if attempt == config.max_generation_attempts:
            logger.error("quality failed after %s attempts, skipping post", attempt)
            return

    logger.info("image prompt generated")
    image_result = generate_image(config, package["image_prompt"], package.get("negative_prompt", ""), logger)
    if not image_result:
        return
    logger.info("image generated: %s", image_result["local_path"])
    hosted_url = upload_image(image_result["local_path"], config)
    logger.info("hosted/public image URL created: %s", hosted_url)
    result = post_to_meta(package["caption"], hosted_url, config, logger)
    logger.info("Facebook posted or failed: %s", result["facebook"]["status"])
    logger.info("Instagram container created/published or failed: %s", result["instagram"]["status"])


def schedule_posts(config, logger):
    interval = max(1, config.post_interval_hours)
    logger.info("scheduler started; posting every %s hour(s)", interval)
    while True:
        run_workflow(config, logger)
        jitter = random.randint(0, max(0, config.randomize_interval_minutes))
        sleep_seconds = (interval * 3600) + (jitter * 60)
        logger.info("sleep time: %s seconds", sleep_seconds)
        time.sleep(sleep_seconds)
