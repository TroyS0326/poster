from scheduler import schedule_posts
from config import load_config

if __name__ == "__main__":
    config = load_config()
    schedule_posts(config)
