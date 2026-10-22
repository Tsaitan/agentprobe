"""合同业务服务的查询与到期筛选测试。"""

from dataclasses import asdict, replace
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


def test_list_customer_contracts_returns_all_matching_contracts(
    service, repository, contract
):
    """查询客户全部合同：保留不同状态和日期的合同，排除其他客户的数据。"""
    cancelled_contract = replace(
        contract, id=1002, status="cancelled", end_date=date(2026, 10, 10)
    )
    other_customer_contract = replace(contract, id=1003, customer_id=102)
    for item in (contract, other_customer_contract, cancelled_contract):
        repository.add(item)

    result = service.list_customer_contracts(101)

    assert len(result) == 2
    assert contract in result
    assert cancelled_contract in result


def test_list_expiring_contracts_filters_mixed_data(service, repository, contract):
    """混合数据查询：只返回目标客户在窗口内有效的合同，排除其他客户及无效合同。"""
    contracts = [
        contract,  # 客户 101，9 天后到期
        replace(contract, id=1002, end_date=date(2026, 11, 5)),  # 14 天后到期
        replace(contract, id=1003, customer_id=102),  # 其他客户
        replace(contract, id=1004, status="cancelled"),  # 已取消
        replace(contract, id=1005, end_date=date(2026, 11, 22)),  # 超出窗口
        replace(contract, id=1006, end_date=date(2026, 10, 21)),  # 已过期
        replace(contract, id=1007, start_date=date(2026, 10, 23)),  # 未开始
    ]
    for item in contracts:
        repository.add(item)

    result = service.list_expiring_contracts(
        customer_id=101,
        days=30,
        on_date=date(2026, 10, 22),
    )

    assert len(result) == 2
    assert {item.id for item in result} == {1001, 1002}


def test_list_expiring_contracts_includes_contract_ending_in_30_days(
    service, repository, contract
):
    """到期窗口上边界：合同恰好在基准日 30 天后到期时，应包含在结果中。"""
    expiring_contract = replace(contract, end_date=date(2026, 11, 21))
    repository.add(expiring_contract)

    result = service.list_expiring_contracts(
        customer_id=101,
        days=30,
        on_date=date(2026, 10, 22),
    )

    assert result == [expiring_contract]


def test_list_expiring_contracts_excludes_contract_ending_in_31_days(
    service, repository, contract
):
    """超出到期窗口：合同在基准日 31 天后到期时，不包含在 30 天查询结果中。"""
    outside_window_contract = replace(contract, end_date=date(2026, 11, 22))
    repository.add(outside_window_contract)

    result = service.list_expiring_contracts(
        customer_id=101,
        days=30,
        on_date=date(2026, 10, 22),
    )

    assert result == []


@pytest.mark.parametrize(
    "has_contract", [True, False], ids=["with-contract", "without-contract"]
)
def test_list_expiring_contracts_rejects_negative_days(
    service, repository, contract, has_contract
):
    """负数窗口：客户有合同或没有合同时，days=-1 均应抛出 ValueError。"""
    if has_contract:
        repository.add(contract)

    with pytest.raises(ValueError, match="days"):
        service.list_expiring_contracts(
            customer_id=101,
            days=-1,
            on_date=date(2026, 10, 22),
        )


@pytest.mark.parametrize(
    "has_other_customer", [False, True], ids=["empty-repository", "other-customer"]
)
def test_list_customer_contracts_returns_empty_for_customer_without_contracts(
    service, repository, contract, has_other_customer
):
    """客户没有合同：仓储为空或只有其他客户数据时，全部合同查询均返回空列表。"""
    if has_other_customer:
        repository.add(replace(contract, customer_id=102))

    result = service.list_customer_contracts(101)

    assert result == []


@pytest.mark.parametrize(
    "has_other_customer", [False, True], ids=["empty-repository", "other-customer"]
)
def test_list_expiring_contracts_returns_empty_for_customer_without_contracts(
    service, repository, contract, has_other_customer
):
    """客户没有合同：仓储为空或只有其他客户数据时，到期合同查询均返回空列表。"""
    if has_other_customer:
        repository.add(replace(contract, customer_id=102))

    result = service.list_expiring_contracts(
        customer_id=101,
        days=30,
        on_date=date(2026, 10, 22),
    )

    assert result == []


def test_list_expiring_contracts_includes_contract_ending_today(
    service, repository, contract
):
    """到期窗口下边界：有效合同在基准日当天到期时，应包含在查询结果中。"""
    ending_today_contract = replace(contract, end_date=date(2026, 10, 22))
    repository.add(ending_today_contract)

    result = service.list_expiring_contracts(
        customer_id=101,
        days=30,
        on_date=date(2026, 10, 22),
    )

    assert result == [ending_today_contract]


def test_list_expiring_contracts_does_not_modify_data(service, repository, contract):
    """查询不修改数据：合同字段、按 ID 存储的数据及客户合同集合均保持不变。"""
    contracts = [
        contract,
        replace(contract, id=1002, status="cancelled"),
        replace(contract, id=1003, end_date=date(2026, 11, 22)),
        replace(contract, id=1004, customer_id=102),
    ]
    for item in contracts:
        repository.add(item)
    # 保存独立字段快照，避免原对象被修改后，预期值也随之变化。
    snapshots = [asdict(item) for item in contracts]

    result = service.list_expiring_contracts(
        customer_id=101,
        days=30,
        on_date=date(2026, 10, 22),
    )

    assert result == [contract]
    assert [asdict(item) for item in contracts] == snapshots
    for snapshot in snapshots:
        stored_contract = repository.get_by_id(snapshot["id"])
        assert stored_contract is not None
        assert asdict(stored_contract) == snapshot
    assert sorted(item.id for item in repository.list_by_customer(101)) == [
        1001,
        1002,
        1003,
    ]
    assert [item.id for item in repository.list_by_customer(102)] == [1004]
