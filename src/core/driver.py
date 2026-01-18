"""封裝 undetected_chromedriver 的初始化與生命週期管理"""

import logging
import time
from contextlib import AbstractContextManager
from typing import Optional

import undetected_chromedriver as uc
from selenium.common.exceptions import WebDriverException
from selenium.webdriver.chrome.options import Options as ChromeOptions

from config import DRIVER_DEFAULTS, load_driver_overrides
from ..models.schemas import DriverConfig
from ..utils.logger import get_logger


class DriverManager(AbstractContextManager):
    """管理 driver 的建立與關閉，並提供重試與 logging。"""

    def __init__(self, config: Optional[DriverConfig] = None, logger: Optional[logging.Logger] = None):
        merged = {**DRIVER_DEFAULTS, **load_driver_overrides()}
        self.config = config or DriverConfig.from_dict(merged)
        self.logger = logger or get_logger(
            __name__, level=self.config.log_level)
        self.driver = None

    def __enter__(self):
        self.start()
        return self.driver

    def __exit__(self, exc_type, exc_value, traceback):
        self.quit()
        return False

    def start(self):
        if self.driver:
            return self.driver

        delay = self.config.retry.initial_delay
        for attempt in range(1, self.config.retry.attempts + 1):
            try:
                options = self._build_options()
                self.logger.info(f"Starting Chrome (attempt {attempt})")
                driver = uc.Chrome(options=options)
                self._apply_timeouts(driver)
                # 強制設定視窗大小
                w, h = self.config.window_size
                driver.set_window_size(w, h)
                self.driver = driver
                self.logger.info("Chrome started successfully")
                return self.driver
            except WebDriverException as exc:  # pragma: no cover - depends on env
                self.logger.warning(
                    f"Chrome start failed: {exc}", exc_info=False)
                if attempt >= self.config.retry.attempts:
                    self.logger.error(
                        f"Chrome failed after {attempt} attempts")
                    raise
                time.sleep(delay)
                delay *= self.config.retry.backoff
        return self.driver

    def quit(self):
        if not self.driver:
            return
        try:
            self.logger.info("Quitting Chrome")
            self.driver.quit()
        except Exception as exc:  # pragma: no cover - best-effort
            self.logger.warning(f"Error during quit: {exc}", exc_info=False)
        finally:
            self.driver = None

    def _build_options(self) -> ChromeOptions:
        options = uc.ChromeOptions()
        if self.config.headless:
            options.add_argument("--headless=new")
        w, h = self.config.window_size
        options.add_argument(f"--window-size={w},{h}")
        options.add_argument("--disable-gpu")
        options.add_argument("--disable-dev-shm-usage")
        options.add_argument("--no-sandbox")
        if self.config.user_agent:
            options.add_argument(f"--user-agent={self.config.user_agent}")
        prefs = {
            "credentials_enable_service": False,
            "profile.password_manager_enabled": False,
            "profile.password_manager_leak_detection": False,
        }
        if self.config.download_dir:
            prefs["download.default_directory"] = self.config.download_dir
            prefs["download.prompt_for_download"] = False
        if prefs:
            options.add_experimental_option("prefs", prefs)
        return options

    def _apply_timeouts(self, driver):
        driver.set_page_load_timeout(self.config.timeouts.page_load)
        driver.implicitly_wait(self.config.timeouts.implicit)
        driver.set_script_timeout(self.config.timeouts.script)
