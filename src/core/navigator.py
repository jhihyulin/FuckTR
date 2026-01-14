"""處理頁面跳轉、等待元素、基礎 DOM 操作。"""

import logging
from typing import Optional, Tuple

from selenium.common.exceptions import TimeoutException
from selenium.webdriver.common.by import By
from selenium.webdriver.remote.webdriver import WebDriver
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.support.ui import WebDriverWait

from ..utils.logger import get_logger


Locator = Tuple[str, str]


class Navigator:
    def __init__(self, driver: WebDriver, default_wait: int = 20, logger: Optional[logging.Logger] = None):
        self.driver = driver
        self.default_wait = default_wait
        self.logger = logger or get_logger(__name__)

    def go_to(self, url: str, wait_ready: bool = True, timeout: Optional[int] = None):
        self.logger.info("Navigate to %s", url)
        self.driver.get(url)
        if wait_ready:
            self.wait_ready(timeout=timeout)

    def wait_ready(self, timeout: Optional[int] = None):
        to = timeout or self.default_wait
        WebDriverWait(self.driver, to).until(
            lambda d: d.execute_script(
                "return document.readyState") == "complete"
        )

    def wait_for(self, locator: Locator, timeout: Optional[int] = None):
        to = timeout or self.default_wait
        by, value = locator
        return WebDriverWait(self.driver, to).until(EC.presence_of_element_located((by, value)))

    def wait_clickable(self, locator: Locator, timeout: Optional[int] = None):
        to = timeout or self.default_wait
        by, value = locator
        return WebDriverWait(self.driver, to).until(EC.element_to_be_clickable((by, value)))

    def click(self, locator: Locator, timeout: Optional[int] = None):
        try:
            el = self.wait_clickable(locator, timeout)
            el.click()
            return el
        except TimeoutException as exc:
            self.logger.error("Click timeout: %s", locator)
            raise exc

    def fill(self, locator: Locator, text: str, clear: bool = True, timeout: Optional[int] = None):
        try:
            el = self.wait_for(locator, timeout)
            if clear:
                el.clear()
            el.send_keys(text)
            return el
        except TimeoutException as exc:
            self.logger.error("Fill timeout: %s", locator)
            raise exc

    @staticmethod
    def by_css(selector: str) -> Locator:
        return (By.CSS_SELECTOR, selector)

    @staticmethod
    def by_xpath(expr: str) -> Locator:
        return (By.XPATH, expr)
