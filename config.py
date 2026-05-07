import os
from dataclasses import dataclass
from dotenv import load_dotenv


@dataclass
class Config:
    image_provider: str
    sd_api_url: str
    replicate_api_token: str
    replicate_model: str
    replicate_output_format: str
    meta_access_token: str
    fb_page_id: str
    ig_business_id: str
    img_public_url_base: str
    gemini_api_key: str
    gemini_model: str
    openai_api_key: str
    meta_graph_version: str
    post_interval_hours: int
    randomize_interval_minutes: int
    log_path: str
    dry_run: bool
    manual_review_mode: bool
    max_generation_attempts: int
    image_width: int
    image_height: int
    sd_model: str


def _to_bool(value: str, default: bool = False) -> bool:
    if value is None:
        return default
    return value.strip().lower() in {"1", "true", "yes", "on"}


def load_config() -> Config:
    load_dotenv()
    return Config(
        image_provider=os.getenv("IMAGE_PROVIDER", "auto1111").strip().lower(),
        sd_api_url=os.getenv("SD_API_URL", "http://127.0.0.1:7860"),
        replicate_api_token=os.getenv("REPLICATE_API_TOKEN", ""),
        replicate_model=os.getenv("REPLICATE_MODEL", "black-forest-labs/flux-schnell"),
        replicate_output_format=os.getenv("REPLICATE_OUTPUT_FORMAT", "jpg").strip().lower() or "jpg",
        meta_access_token=os.getenv("META_ACCESS_TOKEN", ""),
        fb_page_id=os.getenv("FB_PAGE_ID", ""),
        ig_business_id=os.getenv("IG_BUSINESS_ID", ""),
        img_public_url_base=os.getenv("IMG_PUBLIC_URL_BASE", ""),
        gemini_api_key=os.getenv("GEMINI_API_KEY", ""),
        gemini_model=os.getenv("GEMINI_MODEL", "gemini-1.5-flash"),
        openai_api_key=os.getenv("OPENAI_API_KEY", ""),
        meta_graph_version=os.getenv("META_GRAPH_VERSION", "v20.0"),
        post_interval_hours=int(os.getenv("POST_INTERVAL_HOURS", "4")),
        randomize_interval_minutes=int(os.getenv("RANDOMIZE_INTERVAL_MINUTES", "0")),
        log_path=os.getenv("LOG_PATH", "logs/xeanvi_social_bot.log"),
        dry_run=_to_bool(os.getenv("DRY_RUN"), False),
        manual_review_mode=_to_bool(os.getenv("MANUAL_REVIEW_MODE"), False),
        max_generation_attempts=int(os.getenv("MAX_GENERATION_ATTEMPTS", "3")),
        image_width=int(os.getenv("IMAGE_WIDTH", "1080")),
        image_height=int(os.getenv("IMAGE_HEIGHT", "1350")),
        sd_model=os.getenv("SD_MODEL", "dreamshaper_8.safetensors"),
    )


def validate_required_config(config: Config) -> tuple[bool, list[str]]:
    missing = []
    if not config.gemini_api_key:
        missing.append("GEMINI_API_KEY")
    if config.image_provider == "auto1111":
        if not config.sd_api_url:
            missing.append("SD_API_URL")
        if not config.img_public_url_base:
            missing.append("IMG_PUBLIC_URL_BASE")
    if config.image_provider == "replicate":
        if not config.replicate_api_token:
            missing.append("REPLICATE_API_TOKEN")
        if not config.replicate_model:
            missing.append("REPLICATE_MODEL")
    if not config.dry_run and not config.manual_review_mode:
        if not config.meta_access_token:
            missing.append("META_ACCESS_TOKEN")
        if not config.fb_page_id:
            missing.append("FB_PAGE_ID")
        if not config.ig_business_id:
            missing.append("IG_BUSINESS_ID")
    return len(missing) == 0, missing
