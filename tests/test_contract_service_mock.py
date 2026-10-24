"""使用 Mock 仓储隔离验证合同服务的返回结果和调用行为。"""

from dataclasses import replace
from datetime import date
from decimal import Decimal
from unittest.mock import MagicMock

import pytest

from agentprobe.domain.contract import Contract
from agentprobe.repositories.protocol import ContractRepository
from agentprobe.services.contract_service import ContractService


@pytest.fixture
def mock_repository() -> MagicMock:
    """每条测试使用独立的仓储替身，属性范围由 Protocol 限定。"""
    return MagicMock(spec=ContractRepository)


@pytest.fixture
def service(mock_repository: MagicMock) -> ContractService:
    """把模拟仓储注入 Service，不创建真实内存仓储。"""
    return ContractService(mock_repository)


@pytest.fixture
def contract() -> Contract:
    return Contract(
        id=1001,
        customer_id=101,
        name="设备采购合同",
        amount=Decimal("100.00"),
        start_date=date(2026, 10, 1),
        end_date=date(2026, 10, 31),
        status="active",
    )


def test_get_contract_returns_mocked_contract(service, mock_repository, contract):
    """Mock 返回存在的合同：Service 返回该合同，并按正确 ID 查询仓储一次。"""
    mock_repository.get_by_id.return_value = contract

    result = service.get_contract(1001)

    assert result == contract
    mock_repository.get_by_id.assert_called_once_with(1001)


def test_get_contract_returns_none_when_repository_returns_none(
    service, mock_repository
):
    """Mock 查询无结果：Service 返回 None，并按指定 ID 查询仓储一次。"""
    mock_repository.get_by_id.return_value = None

    result = service.get_contract(9999)

    assert result is None
    mock_repository.get_by_id.assert_called_once_with(9999)


def test_list_customer_contracts_returns_mocked_contracts(
    service, mock_repository, contract
):
    """Mock 返回客户全部合同：Service 保留不同状态和日期，并按客户 ID 查询一次。"""
    contracts = [
        contract,
        replace(contract, id=1002, status="cancelled", end_date=date(2026, 10, 10)),
    ]
    mock_repository.list_by_customer.return_value = contracts

    result = service.list_customer_contracts(101)

    assert result == contracts
    mock_repository.list_by_customer.assert_called_once_with(101)


def test_list_expiring_contracts_filters_mocked_contracts(
    service, mock_repository, contract
):
    """Mock 返回混合合同：仅保留窗口内有效合同，并按客户 ID 查询仓储一次。"""
    contracts = [
        contract,  # 7 天后到期
        replace(contract, id=1002, end_date=date(2026, 10, 24)),  # 当天到期
        replace(contract, id=1003, end_date=date(2026, 11, 23)),  # 30 天后到期
        replace(contract, id=1004, end_date=date(2026, 11, 24)),  # 超出窗口
        replace(contract, id=1005, status="cancelled"),  # 日期在窗口内，但已取消
        replace(contract, id=1006, end_date=date(2026, 10, 23)),  # 已过期
        replace(contract, id=1007, start_date=date(2026, 10, 25)),  # 未开始
    ]
    mock_repository.list_by_customer.return_value = contracts

    result = service.list_expiring_contracts(
        customer_id=101,
        days=30,
        on_date=date(2026, 10, 24),
    )

    assert len(result) == 3
    assert {item.id for item in result} == {1001, 1002, 1003}
    mock_repository.list_by_customer.assert_called_once_with(101)


def test_list_expiring_contracts_returns_empty_when_repository_returns_empty(
    service, mock_repository
):
    """Mock 返回空列表：到期查询返回空列表，并按客户 ID 查询仓储一次。"""
    mock_repository.list_by_customer.return_value = []

    result = service.list_expiring_contracts(
        customer_id=101,
        days=30,
        on_date=date(2026, 10, 24),
    )

    assert result == []
    mock_repository.list_by_customer.assert_called_once_with(101)


def test_list_expiring_contracts_rejects_negative_days_without_repository_access(
    service, mock_repository
):
    """负数窗口：抛出 ValueError，且不调用任何仓储查询方法。"""
    with pytest.raises(ValueError, match="days"):
        service.list_expiring_contracts(
            customer_id=101,
            days=-1,
            on_date=date(2026, 10, 24),
        )

    mock_repository.list_by_customer.assert_not_called()
    mock_repository.get_by_id.assert_not_called()
