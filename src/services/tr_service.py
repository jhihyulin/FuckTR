# 主要業務邏輯 (登入、查詢、訂票、查單、退票)

import time
from selenium.common.exceptions import TimeoutException

from ..models.schemas import DriverConfig
from ..utils.logger import get_logger
from ..core.navigator import Navigator


class TRService:
    def __init__(self, driver_config: DriverConfig, navigator: Navigator):
        self.driver_config = driver_config
        self.navigator = navigator
        self.is_logged_in = False
        self.user_info = None
        self.logger = get_logger(__name__)

    def login(self, username: str, password: str) -> bool:
        """登入臺鐵系統"""
        self.logger.info("Attempting to log in user: %s", username)
        try:
            # 填寫登入表單並提交
            self.navigator.go_to(
                "https://www.railway.gov.tw/tra-tip-web/tip/tip008/tip811/memberLogin", wait_ready=True)
            self.logger.debug("Login page loaded")
            # 等 class "blockUI blockOverlay" 消失
            self.navigator.wait_for_element_disappear(
                Navigator.by_css(".blockUI.blockOverlay"))
            self.logger.debug("BlockUI overlay disappeared")
            # 填寫帳號密碼
            self.navigator.wait_clickable(Navigator.by_css("#username"))
            self.logger.debug("Filling in username")
            self.navigator.fill(Navigator.by_css("#username"), username)
            self.navigator.wait_clickable(Navigator.by_css("#password"))
            self.logger.debug("Filling in password")
            self.navigator.fill(Navigator.by_css("#password"), password)
            self.navigator.wait_clickable(Navigator.by_css("#submitBtn"))
            self.logger.debug("Submitting login form")
            self.navigator.click(Navigator.by_css("#submitBtn"))
            # 檢查登入失敗/成功
            success_url = "https://www.railway.gov.tw/tra-tip-web/tip/tip008/tip841/tip841profile"
            error_locator = Navigator.by_css("#errDiv.info-error")
            try:
                self.logger.debug("Waiting for login result")
                result = self.navigator.wait_for_url_or_element(
                    success_url, error_locator, timeout=10)
                if result == 'url':
                    # 登入成功
                    self.is_logged_in = True
                    self.user_info = {"username": username}
                    self.logger.info("Login successful for user: %s", username)
                    return True
                else:
                    # 登入失敗，取得錯誤訊息
                    error_msg = self.navigator.get_element_text(Navigator.by_css(
                        "#errDiv.info-error p.mag-error")) or "Unknown error"
                    self.logger.warning(
                        "Login failed for user %s: %s", username, error_msg)
                    return False
            except TimeoutException:
                self.logger.error("Login timeout for user: %s", username)
                return False
        except Exception as e:
            self.logger.error(
                "Error during login for user %s: %s", username, e)
            return False
