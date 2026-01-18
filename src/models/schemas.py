"""定義資料模型與設定 dataclass"""

from dataclasses import dataclass, field
from enum import Enum
from typing import Optional, Tuple


class OrderSeatPreference(Enum):
    """座位偏好"""
    NONE = "none"
    WINDOW = "window"
    AISLE = "aisle"


@dataclass
class BookOrderData:
    """下訂後取得的訂單資料"""
    ordernum: str
    trainnum: str
    traintype: str
    carriage: str
    seat: str


@dataclass
class Timeouts:
    page_load: int = 30
    implicit: int = 0
    script: int = 30
    wait: int = 20

    @classmethod
    def from_dict(cls, data: dict) -> "Timeouts":
        return cls(
            page_load=data.get("page_load", cls.page_load),
            implicit=data.get("implicit", cls.implicit),
            script=data.get("script", cls.script),
            wait=data.get("wait", cls.wait),
        )


@dataclass
class RetryPolicy:
    attempts: int = 2
    initial_delay: float = 1.0
    backoff: float = 1.5

    @classmethod
    def from_dict(cls, data: dict) -> "RetryPolicy":
        return cls(
            attempts=data.get("attempts", cls.attempts),
            initial_delay=data.get("initial_delay", cls.initial_delay),
            backoff=data.get("backoff", cls.backoff),
        )


@dataclass
class DriverConfig:
    headless: bool = False
    window_size: Tuple[int, int] = (720, 960)
    user_agent: Optional[str] = None
    download_dir: Optional[str] = None
    timeouts: Timeouts = field(default_factory=Timeouts)
    retry: RetryPolicy = field(default_factory=RetryPolicy)
    log_level: str = "INFO"

    @classmethod
    def from_dict(cls, data: dict) -> "DriverConfig":
        return cls(
            headless=data.get("headless", cls.headless),
            window_size=tuple(data.get("window_size", cls.window_size)),
            user_agent=data.get("user_agent"),
            download_dir=data.get("download_dir"),
            timeouts=Timeouts.from_dict(data.get("timeouts", {})),
            retry=RetryPolicy.from_dict(data.get("retry", {})),
            log_level=data.get("log_level", cls.log_level),
        )
