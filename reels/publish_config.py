import os
from dataclasses import dataclass



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



def load_publish_config() -> ReelsPublishConfig:
    return ReelsPublishConfig(
        public_base_url=os.getenv("REELS_PUBLIC_BASE_URL", "").strip(),
        post_dry_run=_env_bool("REELS_POST_DRY_RUN", True),
        post_to_instagram=_env_bool("REELS_POST_TO_INSTAGRAM", True),
        post_to_facebook=_env_bool("REELS_POST_TO_FACEBOOK", False),
    )
