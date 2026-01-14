"""統一 logging 設定。"""

import logging
import os
from typing import Optional


_configured = False


def get_logger(name: str, level: Optional[str] = None) -> logging.Logger:
    global _configured
    if not _configured:
        _setup_logging(level)
        _configured = True
    return logging.getLogger(name)


def _setup_logging(level: Optional[str] = None):
    log_level = (level or os.getenv("LOG_LEVEL", "INFO")).upper()
    logging.basicConfig(
        level=log_level,
        format="%(asctime)s [%(levelname)s] %(name)s - %(message)s",
    )
