import os
from dataclasses import dataclass

from config import load_config


def _env_bool(name: str, default: bool) -> bool:
    raw = os.getenv(name)
    if raw is None:
        return default
    return raw.strip().lower() in {"1", "true", "yes", "on"}


@dataclass
class ReelsPublishConfig:
    public_base_url: str
    post_dry_run: bool
    post_to_instagram: bool
    post_to_facebook: bool
    cleanup_after_success: bool
    delete_after_success_extensions: tuple[str, ...]
    meta_access_token: str
    meta_graph_version: str
    fb_page_id: str
    ig_business_id: str


def _parse_extensions(raw: str) -> tuple[str, ...]:
    exts: list[str] = []
    for item in raw.split(","):
        ext = item.strip().lower()
        if not ext:
            continue
        if not ext.startswith("."):
            ext = f".{ext}"
        exts.append(ext)
    return tuple(exts)


def load_publish_config() -> ReelsPublishConfig:
    app_cfg = load_config()
    return ReelsPublishConfig(
        public_base_url=os.getenv("REELS_PUBLIC_BASE_URL", "").strip(),
        post_dry_run=_env_bool("REELS_POST_DRY_RUN", True),
        post_to_instagram=_env_bool("REELS_POST_TO_INSTAGRAM", True),
        post_to_facebook=_env_bool("REELS_POST_TO_FACEBOOK", True),
        cleanup_after_success=_env_bool("REELS_CLEANUP_AFTER_SUCCESS", True),
        delete_after_success_extensions=_parse_extensions(
            os.getenv("REELS_DELETE_AFTER_SUCCESS_EXTENSIONS", ".mp4,.wav,.mp3,.png")
        ),
        meta_access_token=app_cfg.meta_access_token,
        meta_graph_version=app_cfg.meta_graph_version,
        fb_page_id=app_cfg.fb_page_id,
        ig_business_id=app_cfg.ig_business_id,
    )
