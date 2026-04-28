from apscheduler.schedulers.blocking import BlockingScheduler
from text_ai import generate_caption
from image_ai import generate_image
from uploader import upload_image
from meta_poster import post_to_meta


def job(config):
    print("🚀 Starting XeanVI post workflow...")
    caption = generate_caption(config)
    print("✍️  Generated caption:", caption)

    img_path, img_url, prompt, model_choice = generate_image(config)
    if not img_path:
        print("❌ Image generation failed. Aborting post.")
        return

    print("🖼️  Generated image at:", img_path)
    hosted_url = upload_image(img_path, config)
    print("🌐 Hosted image URL:", hosted_url)
    result = post_to_meta(caption, hosted_url, config)
    print(f"✅ Posted! Result: {result}")


def _get_schedule_times(config):
    # Comma-separated "HH:MM" values, e.g. "09:00,13:30,18:00"
    raw_times = config.get("DAILY_POST_TIMES", "09:00")
    parsed = []
    for value in raw_times.split(","):
        value = value.strip()
        if not value:
            continue
        hour, minute = value.split(":")
        parsed.append((int(hour), int(minute)))
    return parsed or [(9, 0)]


def schedule_posts(config):
    timezone = config.get("SCHEDULER_TIMEZONE", "UTC")
    scheduler = BlockingScheduler(timezone=timezone)
    times = _get_schedule_times(config)

    for hour, minute in times:
        scheduler.add_job(job, "cron", hour=hour, minute=minute, args=[config])
        print(f"🗓️  Scheduled post for {hour:02d}:{minute:02d} ({timezone})")

    print("⏰ XeanVI Daily Scheduler started. Press Ctrl+C to exit.")
    scheduler.start()
