"""臺鐵登入測試"""

import pytest
import os
from dotenv import load_dotenv

from src.core.driver import DriverManager
from src.models.schemas import DriverConfig
from src.services.tr_service import TRService
from src.core.navigator import Navigator


@pytest.mark.tr_login
@pytest.mark.timeout(120)
def test_tr_login_smoke():
    load_dotenv()
    config = DriverConfig(headless=False)
    with DriverManager(config=config) as driver:
        navigator = Navigator(driver=driver)
        tr_service = TRService(driver_config=config, navigator=navigator)
        username = os.getenv("TR_USERNAME")
        password = os.getenv("TR_PASSWORD")
        assert username is not None, "TR_USERNAME 環境變數未設定"
        assert password is not None, "TR_PASSWORD 環境變數未設定"
        login_success = tr_service.login(username=username, password=password)
        assert login_success, "臺鐵登入失敗"
        assert tr_service.is_logged_in, "is_logged_in 標誌未設定為 True"
        assert tr_service.user_info is not None, "user_info 未設定"

@pytest.mark.tr_login_invalid
@pytest.mark.timeout(120)
def test_tr_login_invalid_smoke():
    """使用錯誤的帳號密碼測試登入失敗"""
    config = DriverConfig(headless=False)
    with DriverManager(config=config) as driver:
        navigator = Navigator(driver=driver)
        tr_service = TRService(driver_config=config, navigator=navigator)
        login_success = tr_service.login(username="F123456789", password="abcde12345")
        assert not login_success, "使用無效帳號密碼應該登入失敗"
        assert not tr_service.is_logged_in, "is_logged_in 標誌應為 False"
        assert tr_service.user_info is None, "user_info 應為 None"
