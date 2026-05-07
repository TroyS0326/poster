from config import load_config, validate_required_config
from logger_setup import setup_logger
from scheduler import schedule_posts


if __name__ == "__main__":
    config = load_config()
    logger = setup_logger(config.log_path)
    ok, missing = validate_required_config(config)
    if not ok:
        logger.error("missing required configuration: %s", ", ".join(missing))
        raise SystemExit(1)
    logger.info("XeanVI social bot starting; configured post interval is %s hour(s)", config.post_interval_hours)
    schedule_posts(config, logger)
