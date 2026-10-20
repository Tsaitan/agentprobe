"""内存合同仓储测试。"""

from dataclasses import replace
from datetime import date
from decimal import Decimal

import pytest

from agentprobe.domain.contract import Contract
from agentprobe.repositories.memory_contract_repository import (
    InMemoryContractRepository,
)


@pytest.fixture
def repository() -> InMemoryContractRepository:
    return InMemoryContractRepository()


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


def test_add_contract_successfully(repository, contract):
    """成功添加合同：返回 None，且随后可以按 ID 查询到该合同。"""
    result = repository.add(contract)

    assert result is None
    assert repository.get_by_id(contract.id) == contract


def test_get_by_id_returns_existing_contract(repository, contract):
    """查询已存在的合同：添加 ID 为 1001 的合同后，查询 1001 返回正确合同。"""
    repository.add(contract)

    result = repository.get_by_id(1001)

    assert result == contract


def test_get_by_id_returns_none_for_missing_contract(repository, contract):
    """查询不存在的合同：仓储已有其他合同，查询未添加的 ID 返回 None。"""
    repository.add(contract)

    result = repository.get_by_id(9999)

    assert result is None


def test_add_rejects_duplicate_id_and_preserves_original(repository, contract):
    """重复合同 ID：添加同 ID、其他字段不同的合同会抛出 ValueError，保留原合同。"""
    repository.add(contract)
    duplicate = replace(contract, name="另一份合同", amount=Decimal("200.00"))

    with pytest.raises(ValueError, match="1001"):
        repository.add(duplicate)

    assert repository.get_by_id(1001) == contract


def test_list_by_customer_returns_only_matching_contracts(repository, contract):
    """查询指定客户：只返回客户 101 的两份合同，包含已取消合同，排除客户 102。"""
    second_contract = replace(contract, id=1002, name="续约合同", status="cancelled")
    other_customer_contract = replace(contract, id=1003, customer_id=102)
    for item in (contract, other_customer_contract, second_contract):
        repository.add(item)

    result = repository.list_by_customer(101)

    assert len(result) == 2
    assert {item.id for item in result} == {1001, 1002}
    assert all(item.customer_id == 101 for item in result)


def test_list_by_customer_returns_empty_list_for_missing_customer(repository, contract):
    """查询不存在的客户：仓储已有其他客户的数据，无匹配客户时返回空列表。"""
    repository.add(contract)

    result = repository.list_by_customer(999)

    assert result == []


def test_add_multiple_contracts_with_different_ids(repository, contract):
    """添加多个不同 ID 的合同：每份均可独立按 ID 查询，互不覆盖。"""
    contracts = [
        contract,
        replace(contract, id=1002, name="续约合同"),
        replace(contract, id=1003, customer_id=102, amount=Decimal("200.00")),
    ]
    for item in contracts:
        repository.add(item)

    for item in contracts:
        assert repository.get_by_id(item.id) == item
