"""簡單啟動/關閉的 smoke 測試"""

import pytest

from src.core.driver import DriverManager
from src.core.navigator import Navigator
from src.models.schemas import DriverConfig


@pytest.mark.smoke
@pytest.mark.timeout(60)
def test_driver_starts_and_quits():
    config = DriverConfig(headless=False)
    with DriverManager(config=config) as driver:
        navigator = Navigator(driver=driver)
        navigator.go_to("https://www.example.com", wait_ready=True)
        assert "Example Domain" in driver.title
