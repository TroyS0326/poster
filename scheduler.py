import time
from text_ai import generate_caption
from image_ai import generate_image
from uploader import upload_image
from meta_poster import post_to_meta

def job(config):
    print("🚀 Starting post workflow...")
    caption = generate_caption(config)
    print("✍️  Generated caption:", caption)
    img_path, img_url, mode, model_choice = generate_image(config)
    print("🖼️  Generated image at:", img_path)
    hosted_url = upload_image(img_path, config)
    print("🌐 Hosted image URL:", hosted_url)
    result = post_to_meta(caption, hosted_url, config)
    print(f"✅ Posted! Result: {result}")

def schedule_posts(config):
    # Post every 3 hours exactly (10,800 seconds)
    while True:
        job(config)
        print("😴 Sleeping for 3 hours (10,800 seconds)")
        time.sleep(10800)
