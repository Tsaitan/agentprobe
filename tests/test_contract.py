from datetime import date
from decimal import Decimal

import pytest

from agentprobe.domain.contract import Contract


def make_contract(**overrides) -> Contract:
    data = {
        "id": 1,
        "customer_id": 101,
        "name": "设备采购合同",
        "amount": Decimal("100.00"),
        "start_date": date(2026, 10, 1),
        "end_date": date(2026, 10, 31),
        "status": "active",
    }

    data.update(overrides)

    return Contract(**data)

@pytest.fixture
def active_contract() -> Contract:
    return make_contract()


@pytest.mark.parametrize(
        ("status", "expected"),
        [
            ("active", True),
            ("pending", False),
            ("expired", False),
            ("cancelled", False),
        ]
    )
def test_active_contract_within_date_range(active_contract,status, expected):
    # 准备：创建一份有效期为整个十月的合同
    active_contract.status = status
    assert active_contract.is_active(on_date=date(2026, 10, 15)) is expected

@pytest.mark.parametrize(
    ("on_date", "expected"),
    [
        (date(2026, 9, 30), False),  # 开始前一天
        (date(2026, 10, 1), True),   # 开始当天
        (date(2026, 10, 15), True),  # 有效期内
        (date(2026, 10, 31), True),  # 结束当天
        (date(2026, 11, 1), False),  # 结束后一天
    ],
)
def test_is_active_date_boundaries(active_contract,on_date, expected):
    # 这里放上面创建 contract 的代码
    active_contract.start_date = date(2026, 10, 1)
    active_contract.end_date = date(2026, 10, 31)

    result = active_contract.is_active(on_date=on_date)

    assert result is expected


def test_rejects_negative_amount():
    with pytest.raises(ValueError, match="amount"):
        make_contract(amount=Decimal("-0.01"))

def test_allows_zero_amount():
    contract = make_contract(amount=Decimal("0.00"))

    assert contract.amount == Decimal("0.00")

def test_rejects_end_date_before_start_date():
    with pytest.raises(ValueError, match="start_date"):
        make_contract(
            start_date=date(2026, 10, 31),
            end_date=date(2026, 10, 1),
        )


def test_allows_same_start_and_end_date():
    contract = make_contract(
        start_date=date(2026, 10, 1),
        end_date=date(2026, 10, 1),
    )

    assert contract.start_date == contract.end_date

def test_rejects_invalid_status():
    with pytest.raises(ValueError, match="status"):
        make_contract(status="unknown")

@pytest.mark.parametrize(
    ("start_date", "end_date", "status", "days", "expected"), 
    [
         # 固定基准日为 2026-10-15，默认窗口为 30 天
        (date(2026, 10, 1), date(2026, 10, 15), "active", 30, True),   # 剩余 0 天
        (date(2026, 10, 1), date(2026, 11, 14), "active", 30, True),   # 剩余 30 天
        (date(2026, 10, 1), date(2026, 11, 15), "active", 30, False),  # 剩余 31 天
        (date(2026, 10, 1), date(2026, 10, 14), "active", 30, False),  # 已过期
        (date(2026, 10, 16), date(2026, 10, 20), "active", 30, False), # 未开始
        (date(2026, 10, 1), date(2026, 10, 20), "cancelled", 30, False),
        # days=0：只包含当天到期
        (date(2026, 10, 1), date(2026, 10, 15), "active", 0, True),
        (date(2026, 10, 1), date(2026, 10, 16), "active", 0, False),
    ],ids=[
        "ends-today", # 结束当天
        "ends-in-30-days", # 结束前30天
        "ends-in-31-days", # 结束前31天
        "already-ended", # 已结束
        "not-started", # 未开始
        "cancelled", # 已取消
        "zero-window-ends-today", # 结束当天
        "zero-window-ends-tomorrow", # 明天到期，超出零天窗口
    ],
)
def test_is_expiring_soon(active_contract,start_date, end_date, status, days, expected):
    active_contract.start_date = start_date
    active_contract.end_date = end_date
    active_contract.status = status
    
    assert active_contract.is_expiring_soon(days=days, on_date=date(2026, 10, 15)) is expected  

def test_is_expiring_soon_rejects_negative_days(active_contract):
    active_contract.start_date = date(2026, 10, 1)
    active_contract.end_date = date(2026, 10, 31)
    active_contract.status = "active"

    with pytest.raises(ValueError, match="days"):
        active_contract.is_expiring_soon(
            days=-1,
            on_date=date(2026, 10, 15),
        )