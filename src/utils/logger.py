import logging
import os
import sys
from typing import Optional


def get_logger(name: str, level: Optional[str] = None) -> logging.Logger:
    logger = logging.getLogger(name)
    if level:
        logger.setLevel(getattr(logging, str(level).upper(), logging.INFO))
    else:
        logger.setLevel(logging.NOTSET)
    if not logger.handlers:
        logger.addHandler(logging.NullHandler())
    logger.propagate = True
    return logger


def configure_logging(level: Optional[str] = None, stream=None):
    log_level = (level or os.getenv("LOG_LEVEL", "INFO")).upper()
    root = logging.getLogger()
    if root.handlers:
        root.setLevel(getattr(logging, log_level, logging.INFO))
        return
    logging.basicConfig(
        level=getattr(logging, log_level, logging.INFO),
        format="%(asctime)s [%(levelname)s] %(name)s - %(message)s",
        stream=stream or sys.stderr,
    )
