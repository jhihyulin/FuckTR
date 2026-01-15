"""處理頁面跳轉、等待元素、基礎 DOM 操作"""

import time
import random
import logging
from typing import Optional, Tuple

from selenium.common.exceptions import TimeoutException
from selenium.webdriver.common.by import By
from selenium.webdriver.remote.webdriver import WebDriver
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support.ui import Select

from ..utils.logger import get_logger
from config import config


Locator = Tuple[str, str]


class Navigator:
    def __init__(self, driver: WebDriver, default_wait: int = 20, logger: Optional[logging.Logger] = None):
        self.driver = driver
        self.default_wait = default_wait
        self.logger = logger or get_logger(__name__)

    def go_to(self, url: str, wait_ready: bool = True, timeout: Optional[int] = None):
        self.logger.info(f"Navigate to {url}")
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

    def wait_for_all(self, locator: Locator, timeout: Optional[int] = None):
        to = timeout or self.default_wait
        by, value = locator
        return WebDriverWait(self.driver, to).until(EC.presence_of_all_elements_located((by, value)))

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
            self.logger.error(f"Click timeout: {locator}")
            raise exc

    def click_element(self, element):
        try:
            WebDriverWait(self.driver, self.default_wait).until(
                EC.element_to_be_clickable(element)
            )
            element.click()
            return element
        except TimeoutException as exc:
            self.logger.error("Click element timeout")
            raise exc

    def fill(self, locator: Locator, text: str, clear: bool = True, timeout: Optional[int] = None):
        try:
            el = self.wait_for(locator, timeout)
            if clear:
                el.clear()
            el.send_keys(text)
            return el
        except TimeoutException as exc:
            self.logger.error(f"Fill timeout: {locator}")
            raise exc

    def wait_for_url(self, expected_url: str, timeout: Optional[int] = None) -> bool:
        """等待 URL 變更到指定的 URL"""
        to = timeout or self.default_wait
        try:
            WebDriverWait(self.driver, to).until(
                lambda d: d.current_url == expected_url
            )
            return True
        except TimeoutException:
            return False

    def wait_for_url_or_element(self, expected_url: str, locator: Locator, timeout: Optional[int] = None) -> str:
        """等待 URL 變更或元素出現，返回 'url' 或 'element'"""
        to = timeout or self.default_wait
        by, value = locator
        try:
            WebDriverWait(self.driver, to).until(
                lambda d: d.current_url == expected_url or d.find_elements(
                    by, value)
            )
            if self.driver.current_url == expected_url:
                return 'url'
            else:
                return 'element'
        except TimeoutException as exc:
            self.logger.error(
                f"Timeout waiting for URL '{expected_url}' or element '{locator}'")
            raise exc

    def get_current_url(self) -> str:
        """取得當前頁面 URL"""
        return self.driver.current_url

    def get_element_text(self, locator: Locator, timeout: Optional[int] = None) -> Optional[str]:
        """取得元素的文字內容"""
        try:
            el = self.wait_for(locator, timeout)
            return el.text
        except TimeoutException:
            self.logger.warning(f"Element not found: {locator}")
            return None

    def wait_for_element_disappear(self, locator: Locator, timeout: Optional[int] = None) -> bool:
        """等待元素消失"""
        to = timeout or self.default_wait
        by, value = locator
        try:
            WebDriverWait(self.driver, to).until(
                EC.invisibility_of_element_located((by, value))
            )
            return True
        except TimeoutException:
            self.logger.warning(f"Element did not disappear: {locator}")
            return False

    def select_dropdown_by_value(self, locator: Locator, value: str, timeout: Optional[int] = None):
        """透過值選擇下拉選單選項"""
        try:
            el = self.wait_for(locator, timeout)
            select = Select(el)
            select.select_by_value(value)
            return el
        except TimeoutException as exc:
            self.logger.error(f"Select dropdown timeout: {locator}")
            raise exc

    def random_pause(self):
        """隨機暫停一段時間以模擬人類行為"""
        if not config.get("random_pause", True):
            return
        interval = config.get("random_interval")
        delay = random.uniform(interval[0], interval[1])
        self.logger.info(f"Random pause for {delay:.2f} seconds")
        time.sleep(delay)

    def random_pause_long(self):
        """進行較長時間的隨機暫停"""
        interval = config.get("random_interval_long")
        delay = random.uniform(interval[0], interval[1])
        self.logger.info(f"Random long pause for {delay:.2f} seconds")
        time.sleep(delay)

    @staticmethod
    def by_css(selector: str) -> Locator:
        return (By.CSS_SELECTOR, selector)

    @staticmethod
    def by_xpath(expr: str) -> Locator:
        return (By.XPATH, expr)
