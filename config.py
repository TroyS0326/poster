import os
from dotenv import load_dotenv

def load_config():
    load_dotenv()
    return {
        'OPENAI_API_KEY': os.getenv('OPENAI_API_KEY'),
        'GEMINI_API_KEY': os.getenv('GEMINI_API_KEY'),  # <-- ADD THIS LINE!
        'SD_API_URL': os.getenv('SD_API_URL'),
        'META_ACCESS_TOKEN': os.getenv('META_ACCESS_TOKEN'),
        'FB_PAGE_ID': os.getenv('FB_PAGE_ID'),
        'IG_BUSINESS_ID': os.getenv('IG_BUSINESS_ID'),
        'IMG_PUBLIC_URL_BASE': os.getenv('IMG_PUBLIC_URL_BASE'),
        'LOG_PATH': os.getenv('LOG_PATH', 'logs/auto420bot.log'),
        'POST_INTERVAL_MIN': int(os.getenv('POST_INTERVAL_MIN', 3)),
        'POST_INTERVAL_MAX': int(os.getenv('POST_INTERVAL_MAX', 4)),
        'RANDOMIZE_INTERVAL_MINUTES': int(os.getenv('RANDOMIZE_INTERVAL_MINUTES', 30)),
    }
