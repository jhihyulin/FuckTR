"""pytest 配置與共用 fixture"""

import os
import sys
import pytest
from pathlib import Path
from dotenv import load_dotenv

from src.core.driver import DriverManager
from src.models.schemas import DriverConfig
from src.services.tr_service import TRService
from src.core.navigator import Navigator

PROJECT_ROOT = Path(__file__).parent
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))


def pytest_configure(config):
    """註冊自訂 markers"""
    config.addinivalue_line(
        "markers", "smoke: smoke tests for quick validation"
    )


@pytest.fixture()
def driver_fixture():
    """提供 WebDriver 實例的共用 fixture"""
    from src.core.driver import DriverManager
    from src.models.schemas import DriverConfig

    config = DriverConfig(headless=False)
    with DriverManager(config=config) as driver:
        yield driver


@pytest.fixture()
def login_fixture(driver_fixture):
    """提供已登入臺鐵系統的 TRService 實例"""
    load_dotenv()
    config = DriverConfig(headless=False)
    navigator = Navigator(driver=driver_fixture)
    tr_service = TRService(driver_config=config, navigator=navigator)
    username = os.getenv("TR_USERNAME")
    password = os.getenv("TR_PASSWORD")
    assert username is not None, "TR_USERNAME 環境變數未設定"
    assert password is not None, "TR_PASSWORD 環境變數未設定"
    login_success = tr_service.login(username=username, password=password)
    assert login_success, "臺鐵登入失敗"
    yield tr_service
