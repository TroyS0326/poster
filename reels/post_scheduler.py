from __future__ import annotations
import logging
import os
from datetime import datetime, timedelta

logger = logging.getLogger(__name__)

try:
    import pytz
    AUDIENCE_TZ = pytz.timezone(os.getenv("POSTING_TIMEZONE", "America/Chicago"))
except ImportError:
    import datetime as _dt
    AUDIENCE_TZ = None  # fallback to UTC

DAY_WEIGHTS = {0:2, 1:5, 2:5, 3:3, 4:1, 5:0, 6:0}

REEL_SLOTS  = [(13, 0), (17, 30)]
IMAGE_SLOTS = [(12, 0), (19, 0)]


def _now() -> datetime:
    if AUDIENCE_TZ:
        return datetime.now(AUDIENCE_TZ)
    return datetime.utcnow()


def is_good_posting_time(now: datetime | None = None) -> bool:
    now = now or _now()
    day  = now.weekday()
    hour = now.hour
    if DAY_WEIGHTS.get(day, 0) == 0:
        logger.info("Posting skipped — weekend (day=%d)", day)
        return False
    if hour < 11 or hour >= 21:
        logger.info("Posting skipped — outside hours (hour=%d)", hour)
        return False
    return True


def next_post_window(post_type: str = "reel", now: datetime | None = None) -> datetime:
    now   = now or _now()
    slots = REEL_SLOTS if post_type == "reel" else IMAGE_SLOTS
    for days_ahead in range(14):
        candidate_day = now + timedelta(days=days_ahead)
        if DAY_WEIGHTS.get(candidate_day.weekday(), 0) == 0:
            continue
        for hour, minute in slots:
            candidate = candidate_day.replace(
                hour=hour, minute=minute, second=0, microsecond=0)
            if candidate > now + timedelta(minutes=5):
                return candidate
    # fallback: next Tuesday 1pm
    days_fwd = (1 - now.weekday()) % 7 or 7
    return (now + timedelta(days=days_fwd)).replace(
        hour=13, minute=0, second=0, microsecond=0)


def seconds_until_next_window(post_type: str = "reel") -> float:
    now    = _now()
    target = next_post_window(post_type, now)
    delta  = (target - now).total_seconds()
    logger.info("Next %s window: %s (%dh %dm away)",
                post_type,
                target.strftime("%a %b %d %I:%M%p"),
                int(delta // 3600),
                int((delta % 3600) // 60))
    return max(delta, 60)
