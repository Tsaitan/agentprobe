"""健康检查和合同查询 HTTP API 的响应与参数校验测试。"""

from collections.abc import Iterator
from datetime import date
from decimal import Decimal

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
