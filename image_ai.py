import base64
import os
import random
from datetime import datetime
import requests


def generate_image(config, image_prompt: str, negative_prompt: str, logger):
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
        os.makedirs("images/generated", exist_ok=True)
        filename = f"xeanvi_{datetime.utcnow().strftime('%Y%m%d_%H%M%S')}_{random.randint(1000,9999)}.png"
        local_path = os.path.join("images/generated", filename)
        with open(local_path, "wb") as file:
            file.write(base64.b64decode(data["images"][0]))
        return {"local_path": local_path, "filename": filename, "image_prompt": image_prompt, "model_name": config.sd_model}
    except Exception as exc:
        logger.error("image generation failed: %s", exc)
        return None
