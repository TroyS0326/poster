import hashlib
import json
import os
import random
import time
from quality import validate_caption, validate_image_prompt
from prompts import build_caption, needs_risk_disclosure, should_include_url
from text_ai import (
    _content_history_path,
    _load_content_angle_history,
    _save_content_angle_history,
    generate_content_package,
)
from image_ai import generate_image
from uploader import upload_image
from meta_poster import post_to_meta
from meta_preflight import run_preflight


def _package_fields(package: dict) -> tuple[str | None, str | None, str]:
    if not isinstance(package, dict):
        return None, None, ""
    return package.get("caption"), package.get("image_prompt"), package.get("negative_prompt", "")


def _package_angle(package: dict) -> dict:
    if not isinstance(package, dict):
        return {"pillar": "", "archetype": "", "visual_direction": ""}
    return {
        "pillar": package.get("pillar", ""),
        "archetype": package.get("archetype", ""),
        "visual_direction": package.get("visual_direction", ""),
    }


def _caption_history_path(config):
    log_path = getattr(config, "log_path", "logs/xeanvi_social_bot.log")
    return os.path.join(os.path.dirname(log_path) or ".", "caption_history.json")


def _workflow_ledger_path(config):
    log_path = getattr(config, "log_path", "logs/xeanvi_social_bot.log")
    return os.path.join(os.path.dirname(log_path) or ".", "workflow_runs.jsonl")


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


def _append_workflow_ledger(config, logger, entry):
    path = _workflow_ledger_path(config)
    try:
        os.makedirs(os.path.dirname(path) or ".", exist_ok=True)
        with open(path, "a", encoding="utf-8") as f:
            f.write(json.dumps(entry, ensure_ascii=False, separators=(",", ":")) + "\n")
    except Exception as exc:
        logger.warning("workflow ledger append failed: %s", exc)


def _caption_hash(caption):
    return hashlib.sha256((caption or "").encode("utf-8")).hexdigest()


def _safe_status(result, platform):
    if not isinstance(result, dict):
        return "unknown"
    item = result.get(platform)
    if not isinstance(item, dict):
        return "unknown"
    return str(item.get("status", "unknown"))


def _post_result_summary(result):
    if not isinstance(result, dict):
        return {"facebook": {"status": "unknown"}, "instagram": {"status": "unknown"}}

    def _summ(platform):
        item = result.get(platform, {}) if isinstance(result.get(platform), dict) else {}
        out = {"status": str(item.get("status", "unknown"))}
        for k in ("id", "post_id", "creation_id", "container_id", "reason", "error"):
            if k in item and item[k] is not None:
                out[k] = str(item[k])[:240]
        return out

    return {"facebook": _summ("facebook"), "instagram": _summ("instagram")}


def _post_result_has_success(result):
    return _safe_status(result, "facebook") == "success" or _safe_status(result, "instagram") == "success"


def _record_content_angle_history(config, logger, package):
    angle_history = _load_content_angle_history(config, logger)
    angle_path = _content_history_path(config)
    angle_history.append({**_package_angle(package), "created_at": int(time.time())})
    _save_content_angle_history(angle_path, angle_history, logger)


def run_workflow(config, logger):
    logger.info("workflow started")
    package = None
    caption = None
    image_prompt = None
    negative_prompt = ""
    hosted_url = None
    image_result = None
    validation_reason = None
    history_path, caption_history = _load_caption_history(config, logger)

    base_entry = {
        "created_at": int(time.time()),
        "dry_run": bool(getattr(config, "dry_run", False)),
        "manual_review_mode": bool(getattr(config, "manual_review_mode", False)),
        "pillar": "",
        "archetype": "",
        "visual_direction": "",
        "caption_hash": None,
        "caption_word_count": 0,
        "hashtags": [],
        "image_prompt_hash": None,
        "negative_prompt_hash": None,
        "local_image_path": None,
        "remote_image_url": None,
        "hosted_url": None,
        "facebook_status": "unknown",
        "instagram_status": "unknown",
        "post_result": {},
        "outcome": "",
        "failure_reason": None,
    }

    def record(outcome, failure_reason=None, result=None):
        entry = dict(base_entry)
        if package:
            entry.update(_package_angle(package))
        entry["caption_hash"] = _caption_hash(caption) if caption else None
        entry["caption_word_count"] = len((caption or "").split())
        entry["hashtags"] = [tok for tok in (caption or "").split() if tok.startswith("#")]
        entry["image_prompt_hash"] = _caption_hash(image_prompt) if image_prompt else None
        entry["negative_prompt_hash"] = _caption_hash(negative_prompt) if negative_prompt else None
        if isinstance(image_result, dict):
            entry["local_image_path"] = image_result.get("local_path")
            entry["remote_image_url"] = image_result.get("remote_url")
        entry["hosted_url"] = hosted_url
        entry["facebook_status"] = _safe_status(result, "facebook")
        entry["instagram_status"] = _safe_status(result, "instagram")
        entry["post_result"] = _post_result_summary(result)
        entry["outcome"] = outcome
        entry["failure_reason"] = failure_reason
        _append_workflow_ledger(config, logger, entry)

    for attempt in range(1, config.max_generation_attempts + 1):
        try:
            candidate = generate_content_package(config, logger)
            caption, image_prompt, _ = _package_fields(candidate)
            if not caption or not image_prompt:
                logger.warning("malformed content package on attempt %s", attempt)
                record("skipped_malformed_package", f"attempt_{attempt}: missing caption or image_prompt")
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
                caption, image_prompt, negative_prompt = _package_fields(package)
                break
            validation_reason = f"caption={cap_reason}; image_prompt={prm_reason}"
            record("skipped_validation_failed", validation_reason)
        except Exception as exc:
            logger.exception("workflow attempt %s failed: %s", attempt, exc)

        if attempt == config.max_generation_attempts:
            logger.error("quality/workflow failed after %s attempts, skipping post", attempt)
            return

    if not config.dry_run and not config.manual_review_mode:
        preflight = run_preflight()
        if preflight["fb_page_id"] != "valid" or preflight["ig_business_id"] != "valid":
            logger.error("meta preflight failed: %s", preflight)
            record("skipped_preflight_failed", str(preflight)[:240])
            return

    logger.info("image prompt generated")
    image_result = generate_image(config, image_prompt, negative_prompt, logger)
    if not image_result:
        logger.error("image generation failed, skipping post")
        record("skipped_image_failed", "image generation returned no result")
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
        caption_sig = _caption_hash(caption)
        caption_history = (caption_history + [caption_sig])[-50:]
        _save_caption_history(history_path, caption_history, logger)
        _record_content_angle_history(config, logger, package)
        logger.info("MANUAL_REVIEW_MODE enabled; package=%s image_url=%s", package, hosted_url)
        result = {
            "dry_run": config.dry_run,
            "facebook": {"status": "skipped", "reason": "manual_review_mode"},
            "instagram": {"status": "skipped", "reason": "manual_review_mode"},
        }
        record("manual_review_ready", result=result)
    elif config.dry_run:
        result = {
            "dry_run": True,
            "facebook": {"status": "skipped", "reason": "dry_run"},
            "instagram": {"status": "skipped", "reason": "dry_run"},
        }
        caption_sig = _caption_hash(caption)
        caption_history = (caption_history + [caption_sig])[-50:]
        _save_caption_history(history_path, caption_history, logger)
        _record_content_angle_history(config, logger, package)
        record("dry_run_ready", result=result)
    else:
        result = post_to_meta(caption, hosted_url, config, logger)
        if _post_result_has_success(result):
            caption_sig = _caption_hash(caption)
            caption_history = (caption_history + [caption_sig])[-50:]
            _save_caption_history(history_path, caption_history, logger)
            _record_content_angle_history(config, logger, package)
        fb = _safe_status(result, "facebook")
        ig = _safe_status(result, "instagram")
        if fb == "success" and ig == "success":
            record("posted_success", result=result)
        elif fb == "success" or ig == "success":
            record("posted_partial_success", result=result)
        else:
            record("posted_failed", "both platforms failed", result)

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
