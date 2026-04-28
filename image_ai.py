import requests
import time
import os
import base64
import random

MODEL = "dreamshaper_8.safetensors"

# Realism-focused prompt templates. Edit/add more as you wish!
PROMPTS = [
    # Replace these with what you want most
    "Enter your prompt "
    "Here. make sure"
    "Every line is formatted like this"
    "****************************************************************************************************************** "
    "**************************************************************************************************************************"
    "**********************************************"
]

NEGATIVE = (
    "Enter negative prompts (words) here"
)

def generate_image(config):
    prompt = random.choice(PROMPTS)
    payload = {
        "prompt": prompt,
        "negative_prompt": NEGATIVE,
        "steps": 35,  # up this for more detail if you like
        "width": 1080,
        "height": 1350,
        "sampler_index": "DPM++ 2M Karras",  # Try different samplers if you want even more realism
        "override_settings": {"sd_model_checkpoint": MODEL},
    }

    try:
        r = requests.post(f"{config['SD_API_URL']}/sdapi/v1/txt2img", json=payload)
        r.raise_for_status()
        result = r.json()
        image_b64 = result["images"][0]
        os.makedirs("images", exist_ok=True)
        img_path = f"images/gen_{int(time.time())}.png"
        with open(img_path, "wb") as f:
            f.write(base64.b64decode(image_b64))
        img_url = config['IMG_PUBLIC_URL_BASE'] + os.path.basename(img_path)
        print(f"[REALISM][{MODEL}] Generated image: {img_path}")
        print(f"Prompt used: {prompt}")
        print(f"Public URL: {img_url}")
        return img_path, img_url, prompt, MODEL
    except Exception as e:
        print(f"Error generating image: {e}")
        return None, None, None, MODEL

if __name__ == "__main__":
    config = {
        "SD_API_URL": "http://127.0.0.1:7860",
        "IMG_PUBLIC_URL_BASE": "path to your images",
    }

    num_images = 8
    for i in range(num_images):
        print(f"\n--- Generating image {i+1} of {num_images} ---")
        image_path, image_url, prompt, model_choice = generate_image(config)
        if image_path and image_url:
            print(f"SUCCESS: {image_url}")
        else:
            print("FAILED to generate image.")

    print("\nAll done!")
