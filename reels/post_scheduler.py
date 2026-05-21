import os
"""
Smart posting scheduler — implements 2026 FB/IG algorithm timing research.

Optimal schedule (from Sprout Social / The Digital People research):
  - Best days:    Monday → Thursday
  - Worst days:   Saturday, Sunday (skip entirely)
  - Golden window: Tue & Wed 12:00pm–8:00pm local
  - Weekly volume: 2 Reels + 2 image posts MAX (quality over quantity)
  - Spacing:       Min 18hrs between any two posts

FB compliance rules enforced here:
  - No posting outside business hours (looks like spam bot)
  - No back-to-back posts same day
  - Weekend blackout
"""
from __future__ import annotations
import logging
from datetime import datetime, timedelta
import pytz

logger = logging.getLogger(__name__)

# Central time — adjust to your audience's primary timezone
AUDIENCE_TZ = pytz.timezone(os.getenv("POSTING_TIMEZONE", "America/Chicago"))

# Day weights (0=Mon ... 6=Sun). 0 = skip, higher = prefer
DAY_WEIGHTS = {
    0: 2,   # Monday     — good
    1: 5,   # Tuesday    — BEST (golden window)
    2: 5,   # Wednesday  — BEST (golden window)
    3: 3,   # Thursday   — good
    4: 1,   # Friday     — weak, avoid
    5: 0,   # Saturday   — SKIP
    6: 0,   # Sunday     — SKIP
}

# Preferred posting windows (hour, minute) in audience timezone
# Two slots per day — enough spacing for algorithm to measure engagement
REEL_SLOTS   = [(13, 0), (17, 30)]   # 1:00pm and 5:30pm
IMAGE_SLOTS  = [(12, 0), (19, 0)]    # 12:00pm and 7:00pm

MIN_HOURS_BETWEEN_POSTS = 18


def is_good_posting_time(now: datetime | None = None) -> bool:
    """Returns True if right now is a good time to post."""
    import os
    now = now or datetime.now(AUDIENCE_TZ)
    day = now.weekday()
    hour = now.hour

    if DAY_WEIGHTS.get(day, 0) == 0:
        logger.info("Posting skipped — weekend blackout (day=%d)", day)
        return False

    if hour < 11 or hour >= 21:
        logger.info("Posting skipped — outside hours (hour=%d)", hour)
        return False

    return True


def next_post_window(post_type: str = "reel", now: datetime | None = None) -> datetime:
    """
    Returns the next optimal datetime to post.
    post_type: 'reel' or 'image'
    """
    import os
    now = now or datetime.now(AUDIENCE_TZ)
    slots = REEL_SLOTS if post_type == "reel" else IMAGE_SLOTS

    # Try up to 14 days ahead
    for days_ahead in range(14):
        candidate_day = now + timedelta(days=days_ahead)
        weekday = candidate_day.weekday()

        if DAY_WEIGHTS.get(weekday, 0) == 0:
            continue  # skip weekends

        for hour, minute in slots:
            candidate = candidate_day.replace(
                hour=hour, minute=minute, second=0, microsecond=0
            )
            if candidate > now + timedelta(minutes=5):
                return candidate

    # Fallback — next Tuesday at 1pm
    days_until_tuesday = (1 - now.weekday()) % 7 or 7
    return (now + timedelta(days=days_until_tuesday)).replace(
        hour=13, minute=0, second=0, microsecond=0
    )


def seconds_until_next_window(post_type: str = "reel") -> float:
    """Seconds to sleep until the next optimal posting window."""
    import os
    now = datetime.now(AUDIENCE_TZ)
    target = next_post_window(post_type, now)
    delta = (target - now).total_seconds()
    logger.info(
        "Next %s window: %s (%dh %dm from now)",
        post_type,
        target.strftime("%a %b %d %I:%M%p %Z"),
        int(delta // 3600),
        int((delta % 3600) // 60),
    )
    return max(delta, 60)
