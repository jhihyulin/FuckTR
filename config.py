"""全域預設設定。可由環境變數覆寫部分值

- order_interval/search_interval：輪詢間隔秒數範圍
- driver：瀏覽器啟動與超時設定預設值
"""

import os
from typing import Tuple


# 票務輪詢間隔（秒）
config = {
    "order_interval": [15, 30],
    "search_interval": [5, 10],
}


# Driver 預設設定
DRIVER_DEFAULTS = {
    "headless": False,
    "window_size": (1280, 800),
    "user_agent": None,
    "download_dir": None,
    "timeouts": {
        "page_load": 30,
        "implicit": 0,
        "script": 30,
        "wait": 20,
    },
    "retry": {
        "attempts": 2,
        "initial_delay": 1.0,
        "backoff": 1.5,
    },
    "log_level": os.getenv("LOG_LEVEL", "INFO"),
}


def env_bool(name: str, default: bool) -> bool:
    val = os.getenv(name)
    if val is None:
        return default
    return val.lower() in {"1", "true", "yes", "y"}


def load_driver_overrides() -> dict:
    """從環境變數讀取覆寫選項。"""
    overrides: dict = {}
    if os.getenv("DRIVER_HEADLESS") is not None:
        overrides["headless"] = env_bool(
            "DRIVER_HEADLESS", DRIVER_DEFAULTS["headless"])
    if os.getenv("DRIVER_WINDOW_SIZE"):
        try:
            w, h = os.getenv("DRIVER_WINDOW_SIZE").split("x")
            overrides["window_size"] = (int(w), int(h))
        except Exception:
            pass
    if os.getenv("DRIVER_USER_AGENT"):
        overrides["user_agent"] = os.getenv("DRIVER_USER_AGENT")
    if os.getenv("DRIVER_DOWNLOAD_DIR"):
        overrides["download_dir"] = os.getenv("DRIVER_DOWNLOAD_DIR")
    if os.getenv("DRIVER_PAGELOAD_TIMEOUT"):
        overrides.setdefault("timeouts", {})["page_load"] = int(
            os.getenv("DRIVER_PAGELOAD_TIMEOUT"))
    if os.getenv("DRIVER_WAIT_TIMEOUT"):
        overrides.setdefault("timeouts", {})["wait"] = int(
            os.getenv("DRIVER_WAIT_TIMEOUT"))
    return overrides
