"""臺鐵訂單測試"""

import pytest
import time

from src.core.driver import DriverManager
from src.models.schemas import DriverConfig
from src.services.tr_service import TRService
from src.core.navigator import Navigator


@pytest.mark.tr_order_wait_pay
@pytest.mark.timeout(120)
def test_tr_order_wait_pay(login_fixture):
    """測試取得待付款訂單"""
    tr_service: TRService = login_fixture
    orders = tr_service.fetch_order_wait_pay()
    assert isinstance(orders, list)
    # 每個訂單代碼應為 7 位純數字字串
    for order_code in orders:
        assert isinstance(order_code, str)
        assert len(order_code) == 7
        assert order_code.isdigit()
