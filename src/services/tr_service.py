"""主要業務邏輯 (登入、查詢、訂票、查單、退票)"""

from selenium.common.exceptions import TimeoutException
from selenium.webdriver.common.by import By

from ..models.schemas import DriverConfig, OrderSeatPreference, BookOrderData
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
        self.logger.info(f"Attempting to log in user: {username}")
        try:
            # 填寫登入表單並提交
            self.navigator.go_to(
                "https://www.railway.gov.tw/tra-tip-web/tip/tip008/tip811/memberLogin", wait_ready=True)
            self.logger.info("Login page loaded")
            # 等 class "blockUI blockOverlay" 消失
            self.navigator.wait_for_element_disappear(
                Navigator.by_css(".blockUI.blockOverlay"))
            self.logger.info("BlockUI overlay disappeared")
            # 填寫帳號密碼
            self.navigator.wait_clickable(Navigator.by_css("#username"))
            self.logger.info("Filling in username")
            self.navigator.fill(Navigator.by_css("#username"), username)
            self.navigator.wait_clickable(Navigator.by_css("#password"))
            self.logger.info("Filling in password")
            self.navigator.fill(Navigator.by_css("#password"), password)
            self.navigator.random_pause()
            self.navigator.wait_clickable(Navigator.by_css("#submitBtn"))
            self.logger.info("Submitting login form")
            self.navigator.click(Navigator.by_css("#submitBtn"))
            # 檢查登入失敗/成功
            success_url = "https://www.railway.gov.tw/tra-tip-web/tip/tip008/tip841/tip841profile"
            error_locator = Navigator.by_css("#errDiv.info-error")
            try:
                self.logger.info("Waiting for login result")
                result = self.navigator.wait_for_url_or_element(
                    success_url, error_locator, timeout=10)
                if result == 'url':
                    # 登入成功
                    self.is_logged_in = True
                    self.user_info = {"username": username}
                    self.logger.info(f"Login successful for user: {username}")
                    return True
                else:
                    # 登入失敗，取得錯誤訊息
                    error_msg = self.navigator.get_element_text(Navigator.by_css(
                        "#errDiv.info-error p.mag-error")) or "Unknown error"
                    self.logger.warning(
                        f"Login failed for user {username}: {error_msg}")
                    return False
            except TimeoutException:
                self.logger.error(f"Login timeout for user: {username}")
                return False
        except Exception as e:
            self.logger.error(
                f"Error during login for user {username}: {e}")
            return False

    def _query_orders_wait_pay(self):
        """內部方法：查詢待付款訂單"""
        self.navigator.go_to(
            "https://www.railway.gov.tw/tra-tip-web/tip/tip008/tip851/personView", wait_ready=True)
        self.logger.info("Order search page loaded")
        # 輸入查詢條件並提交
        self.navigator.wait_clickable(
            Navigator.by_css("#queryField"))
        self.logger.info("Selecting 訂單狀態 in dropdown")
        self.navigator.select_dropdown_by_value(
            Navigator.by_css("#queryField"), "ORDER_STATUS")
        self.navigator.wait_clickable(
            Navigator.by_css("#personOrderStatus"))
        self.logger.info("Selecting 未付款 in dropdown")
        self.navigator.select_dropdown_by_value(
            Navigator.by_css("#personOrderStatus"), "ODS1")
        self.navigator.random_pause()
        # 點 submitdiv 子物件 <button>
        self.navigator.wait_clickable(
            Navigator.by_css("#submitdiv button"))
        self.logger.info("Submitting order query form")
        self.navigator.click(Navigator.by_css("#submitdiv button"))
        # 等待結果載入
        # 等 class "blockUI blockOverlay" 消失
        self.navigator.wait_for_element_disappear(
            Navigator.by_css(".blockUI.blockOverlay"))
        self.logger.info("BlockUI overlay disappeared")

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
            self.navigator.random_pause()
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
                    f"Unexpected alert message while fetching orders: {alert_text}")
                raise Exception("Unexpected alert message")
            # 解析訂單列表
            # class"table record-table" 子物件 <tbody> 內的 <tr> 為訂單列
            # 乘車日期	訂票代碼	車廂類型	車次	起訖站	票數	訂單狀態	付款狀態	備註
            rows = self.navigator.wait_for_all(
                Navigator.by_css(".table.record-table tbody tr"))
            self.logger.info(f"Found {len(rows)} order rows")
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
                self.logger.info(f"Found order code: {order_code}")
        except Exception as e:
            self.logger.error(f"Error fetching orders: {e}")
            raise e
        return orders

    def cancel_order_with_ordernum(self, ordernum: str) -> bool:
        """取消指定訂單"""
        # 踢掉未登入狀態
        if not self.is_logged_in:
            self.logger.warning("User not logged in. Cannot fetch orders.")
            raise Exception("User not logged in")
        self.logger.info(f"Cancelling order: {ordernum}")
        try:
            self._query_orders_wait_pay()
            self.navigator.random_pause()
            # 先找 class "alert alert-warning"
            # 若子物件 <p> 內容為 「[查無資料]」，表示無訂單 無法取消
            alert_text = self.navigator.get_element_text(
                Navigator.by_css(".alert.alert-warning p"), timeout=2)
            if alert_text and "[查無資料]" in alert_text:
                self.logger.warning(
                    f"No orders found. Cannot cancel order: {ordernum}")
                raise Exception("找不到指定訂單")
            # 錯誤踢出去
            if alert_text:
                self.logger.warning(
                    f"Unexpected alert message while fetching orders: {alert_text}")
                raise Exception("Unexpected alert message")
            order_btn = None
            # 找到對應訂單的按鈕並點擊
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
                    self.logger.info(f"Found button for order {ordernum}")
                    break
            if not order_btn:
                self.logger.warning(
                    f"Order {ordernum} not found for cancellation")
                return False
            self.navigator.random_pause()
            # 點進入訂單詳情頁
            self.navigator.click_element(order_btn)
            self.logger.info(
                f"Navigated to order detail page for {ordernum}")
            # 等待詳情頁載入
            self.navigator.wait_ready()
            # 點取消訂單按鈕
            self.navigator.wait_clickable(
                Navigator.by_css("#cancel"))
            self.logger.info(f"Clicking cancel button for order {ordernum}")
            self.navigator.click(Navigator.by_css("#cancel"))
            self.navigator.random_pause()
            # 確認取消 class "btn btn-danger"
            self.navigator.wait_clickable(
                Navigator.by_css(".btn.btn-danger"))
            self.logger.info(f"Confirming cancellation for order {ordernum}")
            self.navigator.click(Navigator.by_css(".btn.btn-danger"))
            # 等待取消完成
            self.navigator.wait_ready()
            # 確認 class "alert alert-warning" 有 "已成功取消"
            alert_text = self.navigator.get_element_text(
                Navigator.by_css(".alert.alert-warning p"), timeout=5)
            if alert_text and "已成功取消" in alert_text:
                self.logger.info(f"Order {ordernum} cancelled successfully")
                return True
            else:
                self.logger.warning(
                    f"Cancellation of order {ordernum} may have failed")
        except Exception as e:
            self.logger.error(f"Error cancelling order {ordernum}: {e}")
            raise e
        return False

    def cancel_orders_with_ordernum(self, ordernums: list) -> dict:
        """批次取消多個訂單"""
        results = {}
        for ordernum in ordernums:
            try:
                result = self.cancel_order_with_ordernum(ordernum)
                results[ordernum] = result
                if ordernum != ordernums[-1]:
                    self.navigator.random_pause_long()
            except Exception as e:
                self.logger.error(
                    f"Error cancelling order {ordernum}: {e}")
                results[ordernum] = False
        return results

    def order_with_trainnum(
        self,
        start_station: str,  # 0900-基隆
        end_station: str,  # 1000-臺北
        date: str,  # YYYY/MM/DD
        amount: int,
        trainnum: str,
        seat_preference: OrderSeatPreference = OrderSeatPreference.NONE,
    ) -> BookOrderData:
        """以車次訂票"""
        self.logger.info(
            f"Ordering {amount} tickets from {start_station} to {end_station} on {date} for train {trainnum} with seat preference {seat_preference.value}")
        self.navigator.go_to(
            "https://www.railway.gov.tw/tra-tip-web/tip/tip001/tip123/query", wait_ready=True)
        self.logger.info("Ticket ordering page loaded")
        try:
            # 起始站 id "startStation1"
            self.navigator.wait_clickable(
                Navigator.by_css("#startStation1"))
            self.logger.info(f"Selecting start station: {start_station}")
            self.navigator.fill(
                Navigator.by_css("#startStation1"), start_station)
            # 終點站 id "endStation1"
            self.navigator.wait_clickable(
                Navigator.by_css("#endStation1"))
            self.logger.info(f"Selecting end station: {end_station}")
            self.navigator.fill(
                Navigator.by_css("#endStation1"), end_station)
            # 乘車日期 id "rideDate1" 不能 send_keys 會被干擾 用 JS 直接改 value
            self.navigator.wait_clickable(
                Navigator.by_css("#rideDate1"))
            self.logger.info(f"Selecting ride date: {date}")
            self.navigator.driver.execute_script(
                "document.querySelector('#rideDate1').value = arguments[0];", date)
            # 票數 id "normalQty1"
            self.navigator.wait_clickable(
                Navigator.by_css("#normalQty1"))
            self.logger.info(f"Selecting ticket amount: {amount}")
            self.navigator.fill(
                Navigator.by_css("#normalQty1"), str(amount))
            # 車次 id "trainNoList1"
            self.navigator.wait_clickable(
                Navigator.by_css("#trainNoList1"))
            self.logger.info(f"Selecting train number: {trainnum}")
            self.navigator.fill(
                Navigator.by_css("#trainNoList1"), trainnum)
            # 座位偏好
            if seat_preference == OrderSeatPreference.NONE:
                pass
            elif seat_preference == OrderSeatPreference.WINDOW:
                # 靠窗 <label for=seatPref2>
                self.navigator.wait_clickable(
                    Navigator.by_css("label[for='seatPref2']"))
                self.logger.info("Selecting window seat preference")
                self.navigator.click(
                    Navigator.by_css("label[for='seatPref2']"))
            elif seat_preference == OrderSeatPreference.AISLE:
                # 靠走道 <label for=seatPref3>
                self.navigator.wait_clickable(
                    Navigator.by_css("label[for='seatPref3']"))
                self.logger.info("Selecting aisle seat preference")
                self.navigator.click(
                    Navigator.by_css("label[for='seatPref3']"))
            self.navigator.random_pause()
            # 提交訂票 class "btn-sentgroup" 子物件 <input type="submit">
            self.navigator.wait_clickable(
                Navigator.by_css(".btn-sentgroup input[type='submit']"))
            self.logger.info("Submitting ticket order form")
            self.navigator.click(
                Navigator.by_css(".btn-sentgroup input[type='submit']"))
            self.navigator.wait_ready()
            # 等 id errorDiv 出現或或跳 https://www.railway.gov.tw/tra-tip-web/tip/tip001/tip123/queryTrain
            result = self.navigator.wait_for_url_or_element(
                "https://www.railway.gov.tw/tra-tip-web/tip/tip001/tip123/queryTrain",
                Navigator.by_css("#errorDiv"), timeout=10)
            if result != 'url':
                # 訂票失敗，取得錯誤訊息
                error_msg = self.navigator.get_element_text(
                    Navigator.by_css("#errorDiv p.mag-error")) or "Unknown error"
                self.logger.warning(
                    f"Ticket ordering failed: {error_msg}")
                raise Exception(f"Ticket ordering failed: {error_msg}")
            # 進入選車次頁面
            self.logger.info("Navigated to seat selection page (auto)")
            # 等 class "blockUI blockOverlay" 消失
            self.navigator.wait_for_element_disappear(
                Navigator.by_css(".blockUI.blockOverlay"))
            self.logger.info("BlockUI overlay disappeared")
            # 兩個可能
            # 1. class "search-trip" 有子物件 class "search-trip-mag" 子物件 <p> 包含 「沒有空位」
            # 2. class "search-trip" 有 <table> class "itinerary-controls"
            no_seat_text = self.navigator.get_element_text(
                Navigator.by_css(".search-trip .search-trip-mag p"), timeout=2)
            if no_seat_text and "沒有空位" in no_seat_text:
                self.logger.warning("No available seats found")
                raise Exception("No available seats")
            self.logger.info("Available seats found, proceeding to book")
            # 點 <label for="route00"> 選擇第一個車次
            self.navigator.wait_clickable(
                Navigator.by_css("label[for='route00']"))
            self.logger.info("Selecting first available train route")
            self.navigator.click(
                Navigator.by_css("label[for='route00']"))
            self.navigator.random_pause()
            # 點 class "btn-sentgroup" 子物件 <button type="submit">
            self.navigator.wait_clickable(
                Navigator.by_css(".btn-sentgroup button[type='submit']"))
            self.logger.info("Submitting seat selection form")
            self.navigator.click(
                Navigator.by_css(".btn-sentgroup button[type='submit']"))
            # 付款頁面
            # 兩個可能
            # 1. https://www.railway.gov.tw/tra-tip-web/tip/tip001/tip115/booking/modify 成功繼續下方邏輯
            # 2. https://www.railway.gov.tw/tra-tip-web/tip/tip001/tip123/query 失敗讀 id "errDiv" 取得錯誤訊息
            result = self.navigator.wait_for_url_or_element(
                "https://www.railway.gov.tw/tra-tip-web/tip/tip001/tip115/booking/modify",
                Navigator.by_css("#errDiv"), timeout=10)
            self.logger.info("Navigated to payment page")
            if result != 'url':
                # 訂票失敗，取得錯誤訊息
                error_msg = self.navigator.get_element_text(
                    Navigator.by_css("#errDiv p.mag-error")) or "Unknown error"
                self.logger.warning(
                    f"Ticket ordering failed at payment page: {error_msg}")
                raise Exception(f"Ticket ordering failed: {error_msg}")
            # 等 class "blockUI blockOverlay" 消失
            self.navigator.wait_for_element_disappear(
                Navigator.by_css(".blockUI.blockOverlay"))
            self.logger.info("BlockUI overlay disappeared")
            # 解析訂單資料
            # 找 div class "cartlist-id" > span text 包含訂單編號
            self.logger.info("Retrieving order number from payment page")
            order_num = self.navigator.get_element_text(
                Navigator.by_css(".cartlist-id span"), timeout=5)
            if not order_num:
                self.logger.warning("Order number not found on payment page")
                raise Exception("Order number not found")
            self.logger.info(f"Order number retrieved: {order_num}")
            # 找 span class "seat"
            carriage_seat_text = self.navigator.get_element_text(
                Navigator.by_css(".seat"), timeout=5)
            if not carriage_seat_text:
                self.logger.warning("Carriage and seat information not found")
                raise Exception("Carriage and seat information not found")
            # 解析車次車型
            # th class "train-trips" <th class="train-trips" width="20%">座位：<br>自強(3000) <br>434車次</th>
            train_info_text = self.navigator.get_element_text(
                Navigator.by_css("th.train-trips"), timeout=5)
            if not train_info_text:
                self.logger.warning("Train information not found")
                raise Exception("Train information not found")
            # 解析車次車型 like 自強(3000) 434車次
            # 按換行符分割，<br> 被轉換成 \n
            train_parts = [line.strip()
                           for line in train_info_text.split('\n') if line.strip()]
            if len(train_parts) < 3:
                self.logger.warning(
                    f"Unexpected train info format: {train_info_text}")
                raise Exception("Unexpected train info format")
            train_type = train_parts[1].strip()
            train_number = train_parts[2].replace("車次", "").strip()
            self.logger.info(
                f"Train type: {train_type}, Train number: {train_number}")
            # 解析車廂與座位 like 7車1號 輸出 carriage="7" seat="1"
            if "車" not in carriage_seat_text or "號" not in carriage_seat_text:
                self.logger.warning(
                    f"Unexpected carriage/seat format: {carriage_seat_text}")
                raise Exception("Unexpected carriage/seat format")
            parts = carriage_seat_text.split("車")
            carriage = parts[0]
            seat = parts[1].replace("號", "")
            self.logger.info(
                f"Order placed successfully: ordernum={order_num}, carriage={carriage}, seat={seat}")
            return BookOrderData(
                ordernum=order_num,
                trainnum=train_number,
                traintype=train_type,
                carriage=carriage,
                seat=seat,
            )
        except Exception as e:
            self.logger.error(f"Error placing order: {e}")
            raise e
