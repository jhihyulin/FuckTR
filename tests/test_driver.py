"""簡單啟動/關閉的 smoke 測試"""

import pytest


@pytest.mark.smoke
@pytest.mark.timeout(60)
def test_driver_starts_and_quits(driver_fixture):
    """測試 WebDriver 能否啟動並關閉"""
    driver = driver_fixture
    assert driver is not None, "WebDriver 未成功啟動"
    # 這裡可以進一步檢查 driver 的狀態
    assert driver.session_id is not None, "WebDriver session 未建立"
    # DriverManager 的 context manager 會自動關閉 driver
