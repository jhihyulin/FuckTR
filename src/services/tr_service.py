"""主要業務邏輯 (登入、查詢、訂票、查單、退票)"""

import time
from selenium.common.exceptions import TimeoutException
from selenium.webdriver.common.by import By

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

    def _query_orders_wait_pay(self):
        """內部方法：查詢待付款訂單"""
        self.navigator.go_to(
            "https://www.railway.gov.tw/tra-tip-web/tip/tip008/tip851/personView", wait_ready=True)
        self.logger.debug("Order search page loaded")
        # 輸入查詢條件並提交
        self.navigator.wait_clickable(
            Navigator.by_css("#queryField"))
        self.logger.debug("Selecting 訂單狀態 in dropdown")
        self.navigator.select_dropdown_by_value(
            Navigator.by_css("#queryField"), "ORDER_STATUS")
        self.navigator.wait_clickable(
            Navigator.by_css("#personOrderStatus"))
        self.logger.debug("Selecting 未付款 in dropdown")
        self.navigator.select_dropdown_by_value(
            Navigator.by_css("#personOrderStatus"), "ODS1")
        # 點 submitdiv 子物件 <button>
        self.navigator.wait_clickable(
            Navigator.by_css("#submitdiv button"))
        self.logger.debug("Submitting order query form")
        self.navigator.click(Navigator.by_css("#submitdiv button"))
        # 等待結果載入
        # 等 class "blockUI blockOverlay" 消失
        self.navigator.wait_for_element_disappear(
            Navigator.by_css(".blockUI.blockOverlay"))
        self.logger.debug("BlockUI overlay disappeared")

    def fetch_order_wait_pay(self) -> list:
        """取得未付款訂單列表"""
        # 踢掉未登入狀態
        if not self.is_logged_in:
            self.logger.warning("User not logged in. Cannot fetch orders.")
            raise Exception("User not logged in")
        self.logger.info("Fetching orders waiting for payment")
        orders = []
        try:
            self._query_orders_wait_pay()
            # 先找 class "alert alert-warning"
            # 若子物件 <p> 內容為 「[查無資料]」，表示無訂單 回傳空列表
            alert_text = self.navigator.get_element_text(
                Navigator.by_css(".alert.alert-warning p"), timeout=2)
            if alert_text and "[查無資料]" in alert_text:
                self.logger.info("No orders waiting for payment found")
                return orders
            # 錯誤踢出去
            if alert_text:
                self.logger.warning(
                    "Unexpected alert message while fetching orders: %s", alert_text)
                raise Exception("Unexpected alert message")
            # 解析訂單列表
            # class"table record-table" 子物件 <tbody> 內的 <tr> 為訂單列
            # 乘車日期	訂票代碼	車廂類型	車次	起訖站	票數	訂單狀態	付款狀態	備註
            rows = self.navigator.wait_for_all(
                Navigator.by_css(".table.record-table tbody tr"))
            self.logger.debug("Found %d order rows", len(rows))
            # 僅蒐集訂票代碼
            for row in rows:
                # 略過表頭
                if row.find_elements(By.TAG_NAME, "th"):
                    continue
                cols = row.find_elements(By.TAG_NAME, "td")
                # 取 td > form > button 的內容
                order_code = cols[1].find_element(
                    By.TAG_NAME, "button").text.strip()
                orders.append(order_code)
                self.logger.debug("Found order code: %s", order_code)
        except Exception as e:
            self.logger.error("Error fetching orders: %s", e)
            raise e
        return orders

    def cancel_order_with_ordernum(self, ordernum: str) -> bool:
        """取消指定訂單"""
        # 踢掉未登入狀態
        if not self.is_logged_in:
            self.logger.warning("User not logged in. Cannot fetch orders.")
            raise Exception("User not logged in")
        self.logger.info("Cancelling order: %s", ordernum)
        try:
            self._query_orders_wait_pay()
            # 找到對應訂單的取消按鈕並點擊
            rows = self.navigator.wait_for_all(
                Navigator.by_css(".table.record-table tbody tr"))
            for row in rows:
                # 略過表頭
                if row.find_elements(By.TAG_NAME, "th"):
                    continue
                cols = row.find_elements(By.TAG_NAME, "td")
                current_order_code = cols[1].find_element(
                    By.TAG_NAME, "button").text.strip()
                if current_order_code == ordernum:
                    order_btn = cols[1].find_element(By.TAG_NAME, "button")
                    self.logger.debug("Found button for order %s", ordernum)
                    break
            if not order_btn:
                self.logger.warning(
                    "Order %s not found for cancellation", ordernum)
                return False
            # 點進入訂單詳情頁
            self.navigator.click_element(order_btn)
            self.logger.debug(
                "Navigated to order detail page for %s", ordernum)
            # 等待詳情頁載入
            self.navigator.wait_ready()
            # 點取消訂單按鈕
            self.navigator.wait_clickable(
                Navigator.by_css("#cancel"))
            self.logger.debug("Clicking cancel button for order %s", ordernum)
            self.navigator.click(Navigator.by_css("#cancel"))
            # 確認取消 class "btn btn-danger"
            self.navigator.wait_clickable(
                Navigator.by_css(".btn.btn-danger"))
            self.logger.debug("Confirming cancellation for order %s", ordernum)
            self.navigator.click(Navigator.by_css(".btn.btn-danger"))
            # 等待取消完成
            self.navigator.wait_ready()
            # 確認 class "alert alert-warning" 有 "已成功取消"
            alert_text = self.navigator.get_element_text(
                Navigator.by_css(".alert.alert-warning p"), timeout=5)
            if alert_text and "已成功取消" in alert_text:
                self.logger.info("Order %s cancelled successfully", ordernum)
                return True
            else:
                self.logger.warning(
                    "Cancellation of order %s may have failed", ordernum)
        except Exception as e:
            self.logger.error("Error cancelling order %s: %s", ordernum, e)
            raise e
        return False
