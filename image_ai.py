import base64
import os
import random
import time
from datetime import datetime
import requests


def _generate_filename() -> str:
    return f"xeanvi_{datetime.utcnow().strftime('%Y%m%d_%H%M%S')}_{random.randint(1000,9999)}.png"


def _save_image_bytes(image_bytes: bytes, filename: str) -> str:
    os.makedirs("images/generated", exist_ok=True)
    local_path = os.path.join("images/generated", filename)
    with open(local_path, "wb") as file:
        file.write(image_bytes)
    return local_path


def generate_image_auto1111(config, image_prompt: str, negative_prompt: str, logger):
    payload = {
        "prompt": image_prompt,
        "negative_prompt": negative_prompt,
        "steps": 30,
        "width": config.image_width,
        "height": config.image_height,
        "override_settings": {"sd_model_checkpoint": config.sd_model},
    }
    try:
        response = requests.post(f"{config.sd_api_url}/sdapi/v1/txt2img", json=payload, timeout=120)
        response.raise_for_status()
        data = response.json()
        if not data.get("images"):
            logger.error("image generation failed: no images returned")
            return None
        filename = _generate_filename()
        local_path = _save_image_bytes(base64.b64decode(data["images"][0]), filename)
        return {"local_path": local_path, "filename": filename, "image_prompt": image_prompt, "model_name": config.sd_model}
    except Exception as exc:
        logger.error("image generation failed: %s", exc)
        return None


def generate_image_replicate(config, image_prompt: str, negative_prompt: str, logger):
    model_path = (config.replicate_model or "").strip()
    if not model_path or "/" not in model_path:
        logger.error("replicate image generation failed: invalid REPLICATE_MODEL '%s'", model_path)
        return None
    owner, model = model_path.split("/", 1)
    headers = {
        "Authorization": f"Bearer {config.replicate_api_token}",
        "Content-Type": "application/json",
    }
    payload = {
        "input": {
            "prompt": image_prompt,
            "negative_prompt": negative_prompt,
            "output_format": config.replicate_output_format or "jpg",
        }
    }

    # Retry up to 3 times on 429 rate limit
    create_response = None
    for attempt in range(3):
        try:
            create_response = requests.post(
                f"https://api.replicate.com/v1/models/{owner}/{model}/predictions",
                json=payload,
                headers=headers,
                timeout=60,
            )
        except requests.RequestException as exc:
            logger.error("replicate request failed: %s", exc)
            return None

        if create_response.status_code == 429:
            try:
                retry_data = create_response.json()
                wait = int(retry_data.get("retry_after", 10)) + 2
            except Exception:
                wait = 12
            logger.warning("replicate rate limited (attempt %d/3), waiting %ds", attempt + 1, wait)
            time.sleep(wait)
            continue

        break

    if create_response is None:
        return None

    if create_response.status_code in {401, 403}:
        logger.error("replicate authentication failed; check REPLICATE_API_TOKEN")
        return None
    if not create_response.ok:
        try:
            error_body = create_response.json()
        except ValueError:
            error_body = create_response.text
        logger.error("replicate create prediction failed with status %s: %s",
                     create_response.status_code, error_body)
        return None

    prediction = create_response.json()
    prediction_id = prediction.get("id")
    if not prediction_id:
        logger.error("replicate image generation failed: prediction id missing")
        return None

    deadline = datetime.utcnow().timestamp() + 180
    status = prediction.get("status")
    while status not in {"succeeded", "failed", "canceled"}:
        if datetime.utcnow().timestamp() > deadline:
            logger.error("replicate image generation failed: polling timeout")
            return None
        poll_response = requests.get(
            f"https://api.replicate.com/v1/predictions/{prediction_id}",
            headers=headers,
            timeout=30,
        )
        if poll_response.status_code in {401, 403}:
            logger.error("replicate authentication failed; check REPLICATE_API_TOKEN")
            return None
        poll_response.raise_for_status()
        prediction = poll_response.json()
        status = prediction.get("status")
        if status not in {"succeeded", "failed", "canceled"}:
            time.sleep(2)

    if status != "succeeded":
        logger.error("replicate image generation failed with status: %s", status)
        return None

    output = prediction.get("output")
    if isinstance(output, list):
        image_url = output[0] if output else None
    else:
        image_url = output
    if not image_url:
        logger.error("replicate image generation failed: no output URL returned")
        return None

    image_response = requests.get(image_url, timeout=60)
    image_response.raise_for_status()
    filename = _generate_filename()
    local_path = _save_image_bytes(image_response.content, filename)
    return {
        "local_path": local_path,
        "filename": filename,
        "image_prompt": image_prompt,
        "model_name": config.replicate_model,
        "remote_url": image_url,
    }


def generate_image(config, image_prompt: str, negative_prompt: str, logger):
    if config.image_provider == "replicate":
        return generate_image_replicate(config, image_prompt, negative_prompt, logger)
    return generate_image_auto1111(config, image_prompt, negative_prompt, logger)
