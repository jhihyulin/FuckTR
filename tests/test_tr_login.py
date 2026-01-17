"""臺鐵登入測試"""

import pytest

from src.models.schemas import DriverConfig
from src.services.tr_service import TRService
from src.core.navigator import Navigator


@pytest.mark.tr_login
@pytest.mark.timeout(120)
def test_tr_login_smoke(login_fixture):
    """使用有效的帳號密碼測試登入成功"""
    tr_service = login_fixture
    assert tr_service.is_logged_in, "is_logged_in 標誌應為 True"
    assert tr_service.user_info is not None, "user_info 不應為 None"


@pytest.mark.tr_login_invalid
@pytest.mark.timeout(120)
def test_tr_login_invalid_smoke(driver_fixture):
    """使用錯誤的帳號密碼測試登入失敗"""
    navigator = Navigator(driver=driver_fixture)
    tr_service = TRService(driver_config=DriverConfig(
        headless=False), navigator=navigator)
    login_success = tr_service.login(
        username="F123456789", password="abcde12345")
    assert not login_success, "使用無效帳號密碼應該登入失敗"
    assert not tr_service.is_logged_in, "is_logged_in 標誌應為 False"
    assert tr_service.user_info is None, "user_info 應為 None"
