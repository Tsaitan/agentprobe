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
