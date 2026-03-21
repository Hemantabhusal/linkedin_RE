import logging
import sys


LOG_FORMAT = "[%(asctime)s] [%(levelname)s] %(name)s: %(message)s"


def configure_logging(level: str = "INFO", verbose: bool = False) -> None:
    root_logger = logging.getLogger()
    root_logger.handlers.clear()
    handler = logging.StreamHandler(sys.stdout)
    handler.setFormatter(logging.Formatter(LOG_FORMAT))
    root_logger.addHandler(handler)
    root_logger.setLevel("DEBUG" if verbose else level.upper())


def get_logger(name: str) -> logging.Logger:
    return logging.getLogger(name)
