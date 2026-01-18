"""臺鐵訂單測試"""

import time
import pytest

from src.models.schemas import BookOrderData, OrderSeatPreference
from src.services.tr_service import TRService


@pytest.mark.tr_order_wait_pay
@pytest.mark.timeout(120)
def test_tr_order_wait_pay(login_fixture: TRService):
    """測試取得待付款訂單"""
    tr_service: TRService = login_fixture
    orders = tr_service.fetch_order_wait_pay()
    assert isinstance(orders, list)
    # 每個訂單代碼應為 7 位純數字字串
    for order_code in orders:
        assert isinstance(order_code, str)
        assert len(order_code) == 7
        assert order_code.isdigit()
    print(f"待付款訂單代碼列表: {orders}")


@pytest.mark.tr_order_cancel
@pytest.mark.timeout(180)
def test_tr_order_cancel(login_fixture: TRService):
    """測試取消待付款訂單"""
    tr_service: TRService = login_fixture
    orders = tr_service.fetch_order_wait_pay()
    if not orders:
        pytest.skip("無待付款訂單可供測試取消")
    order_to_cancel = orders[0]
    result = tr_service.cancel_order_with_ordernum(order_to_cancel)
    assert result is True
    print(f"已取消訂單代碼: {order_to_cancel}")


@pytest.mark.tr_order_cancel_invalid
@pytest.mark.timeout(120)
def test_tr_order_cancel_invalid(login_fixture: TRService):
    """測試取消不存在的訂單"""
    tr_service: TRService = login_fixture
    invalid_order_num = "9999999"  # 假設此訂單號碼不存在
    with pytest.raises(Exception) as exc_info:
        tr_service.cancel_order_with_ordernum(invalid_order_num)
    assert "找不到指定訂單" in str(exc_info.value)
    print(f"取消不存在訂單代碼 {invalid_order_num} 測試通過，捕捉到異常: {exc_info.value}")


@pytest.mark.tr_order_cancel_list
@pytest.mark.timeout(300)
def test_tr_order_cancel_list(login_fixture: TRService):
    """測試批次取消待付款訂單"""
    tr_service: TRService = login_fixture
    orders = tr_service.fetch_order_wait_pay()
    if len(orders) < 2:
        pytest.skip("待付款訂單數量不足以測試批次取消")
    # 取消所有待付款訂單
    results = tr_service.cancel_orders_with_ordernum(orders)
    assert all(results.values()) is True
    print(f"已批次取消訂單代碼: {orders}")


@pytest.mark.tr_order_with_trainnum
@pytest.mark.timeout(180)
def test_tr_order_with_trainnum(login_fixture: TRService):
    """測試取得指定車次的待付款訂單"""
    tr_service: TRService = login_fixture
    start_station = "1000-臺北"
    end_station = "6240-志學"
    date = time.strftime("%Y/%m/%d", time.localtime(time.time() + 15 * 86400))
    amount = 1
    trainnum = "434"
    seat_preference = OrderSeatPreference.WINDOW
    order_data: BookOrderData = tr_service.order_with_trainnum(
        start_station, end_station, date, amount, trainnum, seat_preference
    )
    assert isinstance(order_data, BookOrderData)
    assert isinstance(order_data.ordernum, str)
    assert len(order_data.ordernum) == 7
    assert isinstance(order_data.carriage, str)
    assert order_data.carriage.isdigit()
    assert isinstance(order_data.seat, str)
    assert any(char.isdigit() for char in order_data.seat)
    assert isinstance(order_data.trainnum, str)
    assert isinstance(order_data.traintype, str)
    print(
        f"成功下訂，訂單號碼: {order_data.ordernum}, 車次: {order_data.trainnum}, 車種: {order_data.traintype}, 車廂: {order_data.carriage}, 座位: {order_data.seat}"
    )
