from config import load_config, validate_required_config
from logger_setup import setup_logger
from scheduler import run_workflow


def main():
    config = load_config()
    logger = setup_logger(config.log_path)
    ok, missing = validate_required_config(config)
    if not ok:
        logger.error("missing required configuration: %s", ", ".join(missing))
        raise SystemExit(1)
    logger.info("XeanVI social bot running one workflow attempt via post_once")
    run_workflow(config, logger)


if __name__ == "__main__":
    main()
