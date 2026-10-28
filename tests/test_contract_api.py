"""健康检查和合同查询 HTTP API 的响应与参数校验测试。"""

from collections.abc import Iterator
from dataclasses import replace
from datetime import date, timedelta
from decimal import Decimal
from unittest.mock import MagicMock

import pytest
from fastapi.testclient import TestClient

from agentprobe.api.main import create_app
from agentprobe.domain.contract import Contract
from agentprobe.repositories.memory_contract_repository import (
    InMemoryContractRepository,
)


@pytest.fixture
def repository() -> InMemoryContractRepository:
    """为每条测试创建独立的空仓储。"""
    return InMemoryContractRepository()


@pytest.fixture
def contract() -> Contract:
    """提供用于验证响应字段的固定合同数据。"""
    return Contract(
        id=1001,
        customer_id=101,
        name="设备采购合同",
        amount=Decimal("50000.00"),
        start_date=date(2026, 1, 1),
        end_date=date(2026, 11, 10),
        status="active",
    )


@pytest.fixture
def on_date() -> date:
    """固定到期判断日期，避免测试结果随实际运行日期变化。"""
    return date(2026, 10, 28)


@pytest.fixture
def client(repository: InMemoryContractRepository) -> Iterator[TestClient]:
    """使用测试仓储创建应用，并在测试结束后关闭客户端。"""
    app = create_app(repository)
    with TestClient(app) as test_client:
        yield test_client


def test_health_returns_ok(client: TestClient) -> None:
    """健康检查：返回 200 和约定的状态 JSON。"""
    response = client.get("/health")

    assert response.status_code == 200
    assert response.json() == {"status": "ok"}


def test_get_contract_returns_existing_contract(
    client: TestClient,
    repository: InMemoryContractRepository,
    contract: Contract,
) -> None:
    """查询存在的合同：返回 200、完整字段及字符串格式的金额和日期。"""
    repository.add(contract)

    response = client.get("/contracts/1001")

    assert response.status_code == 200
    assert response.json() == {
        "id": 1001,
        "customer_id": 101,
        "name": "设备采购合同",
        "amount": "50000.00",
        "start_date": "2026-01-01",
        "end_date": "2026-11-10",
        "status": "active",
    }


def test_get_contract_returns_404_for_missing_contract(
    client: TestClient,
    repository: InMemoryContractRepository,
    contract: Contract,
) -> None:
    """查询不存在的合同：仓储已有其他合同，未添加的 ID 返回 404。"""
    repository.add(contract)

    response = client.get("/contracts/9999")

    assert response.status_code == 404
    assert response.json() == {"detail": "合同不存在"}


@pytest.mark.parametrize(
    ("contract_id", "error_type"),
    [
        ("-1", "greater_than"),
        ("0", "greater_than"),
        ("abc", "int_parsing"),
    ],
    ids=["negative-id", "zero-id", "non-numeric-id"],
)
def test_get_contract_rejects_invalid_id(
    client: TestClient, contract_id: str, error_type: str
) -> None:
    """非法 ID：负数、零和非数字返回 422，并指出路径参数的具体错误。"""
    response = client.get(f"/contracts/{contract_id}")

    assert response.status_code == 422
    errors = response.json()["detail"]
    assert len(errors) == 1
    assert errors[0]["loc"] == ["path", "contract_id"]
    assert errors[0]["type"] == error_type


def test_list_customer_contracts_returns_only_matching_customer(
    client: TestClient,
    repository: InMemoryContractRepository,
    contract: Contract,
) -> None:
    """客户合同列表：只返回目标客户，保留已取消和已过期日期的合同，序列化正确。"""
    contracts = [
        contract,
        replace(contract, id=1002, status="cancelled", end_date=date(2026, 1, 2)),
        replace(contract, id=1003, customer_id=102),
    ]
    for item in contracts:
        repository.add(item)

    response = client.get("/customers/101/contracts")

    assert response.status_code == 200
    payload = response.json()
    assert len(payload) == 2
    by_id = {item["id"]: item for item in payload}
    assert set(by_id) == {1001, 1002}
    assert by_id[1001] == {
        "id": 1001,
        "customer_id": 101,
        "name": "设备采购合同",
        "amount": "50000.00",
        "start_date": "2026-01-01",
        "end_date": "2026-11-10",
        "status": "active",
    }
    assert by_id[1002]["status"] == "cancelled"
    assert by_id[1002]["end_date"] == "2026-01-02"


def test_list_customer_contracts_returns_empty_for_unmatched_customer(
    client: TestClient,
    repository: InMemoryContractRepository,
    contract: Contract,
) -> None:
    """无匹配客户：仓储有其他客户的合同，查询返回 200 和空数组。"""
    repository.add(contract)

    response = client.get("/customers/9999/contracts")

    assert response.status_code == 200
    assert response.json() == []


@pytest.mark.parametrize(
    ("suffix", "method_name"),
    [
        ("", "list_customer_contracts"),
        ("/expiring", "list_expiring_contracts"),
    ],
    ids=["customer-list", "expiring-list"],
)
@pytest.mark.parametrize(
    ("customer_id", "error_type"),
    [("0", "greater_than"), ("-1", "greater_than"), ("abc", "int_parsing")],
    ids=["zero-id", "negative-id", "non-numeric-id"],
)
def test_customer_contract_routes_reject_invalid_customer_id(
    client: TestClient,
    monkeypatch: pytest.MonkeyPatch,
    suffix: str,
    method_name: str,
    customer_id: str,
    error_type: str,
) -> None:
    """非法客户 ID：两个列表接口均返回 422，且不调用对应的 Service 查询方法。"""
    query = MagicMock()
    monkeypatch.setattr(client.app.state.contract_service, method_name, query)

    response = client.get(f"/customers/{customer_id}/contracts{suffix}")

    assert response.status_code == 422
    errors = response.json()["detail"]
    assert len(errors) == 1
    assert errors[0]["loc"] == ["path", "customer_id"]
    assert errors[0]["type"] == error_type
    query.assert_not_called()


def test_list_expiring_contracts_filters_mixed_data(
    client: TestClient,
    repository: InMemoryContractRepository,
    contract: Contract,
    on_date: date,
) -> None:
    """混合数据：只返回目标客户窗口内有效合同，排除无效状态、日期和其他客户。"""
    contracts = [
        contract,
        replace(contract, id=1002, end_date=on_date + timedelta(days=30)),
        replace(contract, id=1003, customer_id=102),
        replace(contract, id=1004, status="cancelled"),
        replace(contract, id=1005, end_date=on_date - timedelta(days=1)),
        replace(contract, id=1006, start_date=on_date + timedelta(days=1)),
        replace(contract, id=1007, end_date=on_date + timedelta(days=31)),
        replace(contract, id=1008, status="pending"),
        replace(contract, id=1009, status="expired"),
    ]
    for item in contracts:
        repository.add(item)

    response = client.get(
        "/customers/101/contracts/expiring",
        params={"days": 30, "on_date": on_date.isoformat()},
    )

    assert response.status_code == 200
    payload = response.json()
    assert len(payload) == 2
    by_id = {item["id"]: item for item in payload}
    assert set(by_id) == {1001, 1002}
    assert by_id[1001] == {
        "id": 1001,
        "customer_id": 101,
        "name": "设备采购合同",
        "amount": "50000.00",
        "start_date": "2026-01-01",
        "end_date": "2026-11-10",
        "status": "active",
    }


@pytest.mark.parametrize(
    ("remaining_days", "expected_ids"),
    [(0, [1001]), (30, [1001]), (31, [])],
    ids=["ends-today", "ends-in-30-days", "ends-in-31-days"],
)
def test_list_expiring_contracts_date_boundaries(
    client: TestClient,
    repository: InMemoryContractRepository,
    contract: Contract,
    on_date: date,
    remaining_days: int,
    expected_ids: list[int],
) -> None:
    """到期窗口边界：剩余 0 和 30 天应包含，31 天应排除。"""
    repository.add(replace(contract, end_date=on_date + timedelta(days=remaining_days)))

    response = client.get(
        "/customers/101/contracts/expiring",
        params={"days": 30, "on_date": on_date.isoformat()},
    )

    assert response.status_code == 200
    assert [item["id"] for item in response.json()] == expected_ids


@pytest.mark.parametrize(
    ("days", "expected_ids"),
    [(0, {1001}), (1, {1001, 1002})],
    ids=["zero-day-window", "one-day-window"],
)
def test_list_expiring_contracts_respects_custom_window(
    client: TestClient,
    repository: InMemoryContractRepository,
    contract: Contract,
    on_date: date,
    days: int,
    expected_ids: set[int],
) -> None:
    """自定义窗口：0 天只返回当天到期，1 天包含明天到期并排除后天到期。"""
    for contract_id, remaining in ((1001, 0), (1002, 1), (1003, 2)):
        repository.add(
            replace(
                contract,
                id=contract_id,
                end_date=on_date + timedelta(days=remaining),
            )
        )

    response = client.get(
        "/customers/101/contracts/expiring",
        params={"days": days, "on_date": on_date.isoformat()},
    )

    assert response.status_code == 200
    payload = response.json()
    assert len(payload) == len(expected_ids)
    assert {item["id"] for item in payload} == expected_ids


def test_list_expiring_contracts_defaults_to_30_days(
    client: TestClient,
    repository: InMemoryContractRepository,
    contract: Contract,
    on_date: date,
) -> None:
    """默认窗口：省略 days，包含剩余 30 天的合同，排除剩余 31 天的合同。"""
    repository.add(replace(contract, end_date=on_date + timedelta(days=30)))
    repository.add(replace(contract, id=1002, end_date=on_date + timedelta(days=31)))

    response = client.get(
        "/customers/101/contracts/expiring", params={"on_date": on_date.isoformat()}
    )

    assert response.status_code == 200
    assert [item["id"] for item in response.json()] == [1001]


@pytest.mark.parametrize(
    "customer_id", [101, 9999], ids=["no-expiring-contract", "unmatched-customer"]
)
def test_list_expiring_contracts_returns_empty_when_nothing_matches(
    client: TestClient,
    repository: InMemoryContractRepository,
    contract: Contract,
    on_date: date,
    customer_id: int,
) -> None:
    """空结果：客户的合同均不满足条件，或没有匹配客户时，返回 200 和空数组。"""
    repository.add(replace(contract, status="cancelled"))

    response = client.get(
        f"/customers/{customer_id}/contracts/expiring",
        params={"on_date": on_date.isoformat()},
    )

    assert response.status_code == 200
    assert response.json() == []


@pytest.mark.parametrize(
    ("params", "parameter", "error_type"),
    [
        ({"days": -1}, "days", "greater_than_equal"),
        ({"days": "abc"}, "days", "int_parsing"),
        ({"on_date": "2026-02-30"}, "on_date", None),
        ({"on_date": "invalid"}, "on_date", None),
    ],
    ids=["negative-days", "non-integer-days", "impossible-date", "invalid-date"],
)
def test_list_expiring_contracts_rejects_invalid_query_parameters(
    client: TestClient,
    monkeypatch: pytest.MonkeyPatch,
    params: dict[str, str | int],
    parameter: str,
    error_type: str | None,
) -> None:
    """非法查询参数：返回 422 和准确的错误位置，且不调用 Service 查询方法。"""
    query = MagicMock()
    monkeypatch.setattr(
        client.app.state.contract_service, "list_expiring_contracts", query
    )

    response = client.get("/customers/101/contracts/expiring", params=params)

    assert response.status_code == 422
    errors = response.json()["detail"]
    assert len(errors) == 1
    assert errors[0]["loc"] == ["query", parameter]
    if error_type is not None:
        assert errors[0]["type"] == error_type
    query.assert_not_called()


def test_list_expiring_contracts_defaults_to_controlled_today(
    client: TestClient,
    repository: InMemoryContractRepository,
    contract: Contract,
    on_date: date,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    """默认判断日期：省略 on_date，使用受控的当天，0 天窗口只返回当天到期合同。"""

    class FixedDate(date):
        @classmethod
        def today(cls) -> date:
            return on_date

    monkeypatch.setattr("agentprobe.services.contract_service.date", FixedDate)
    repository.add(replace(contract, end_date=on_date))
    repository.add(replace(contract, id=1002, end_date=on_date + timedelta(days=1)))

    response = client.get("/customers/101/contracts/expiring", params={"days": 0})

    assert response.status_code == 200
    assert [item["id"] for item in response.json()] == [1001]
