"""簡單啟動/關閉的 smoke 測試。"""

import pytest

from src.core.driver import DriverManager
from src.models.schemas import DriverConfig


@pytest.mark.smoke
@pytest.mark.timeout(60)
def test_driver_starts_and_quits():
    # 開啟視窗模式
    config = DriverConfig(headless=False)
    with DriverManager(config=config) as driver:
        driver.get("https://www.google.com")
