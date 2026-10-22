"""合同业务服务的查询与到期筛选测试。"""

from datetime import date
from decimal import Decimal

import pytest

from agentprobe.domain.contract import Contract
from agentprobe.repositories.memory_contract_repository import (
    InMemoryContractRepository,
)
from agentprobe.services.contract_service import ContractService


@pytest.fixture
def repository() -> InMemoryContractRepository:
    return InMemoryContractRepository()


@pytest.fixture
def service(repository: InMemoryContractRepository) -> ContractService:
    return ContractService(repository)


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


def test_get_contract_returns_existing_contract(service, repository, contract):
    """查询存在的合同：从注入的仓储中返回 ID 为 1001 的正确合同。"""
    repository.add(contract)

    result = service.get_contract(1001)

    assert result == contract


def test_get_contract_returns_none_for_missing_contract(service, repository, contract):
    """查询不存在的合同：仓储已有其他合同，未添加的 ID 返回 None。"""
    repository.add(contract)

    result = service.get_contract(9999)

    assert result is None
