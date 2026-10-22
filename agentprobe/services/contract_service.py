"""协调合同查询和领域规则的业务服务。"""

from datetime import date

from agentprobe.domain.contract import Contract
from agentprobe.repositories.memory_contract_repository import (
    InMemoryContractRepository,
)


class ContractService:
    """使用外部传入的仓储组织合同业务操作。"""

    def __init__(self, repository: InMemoryContractRepository) -> None:
        self.repository = repository

    def get_contract(self, contract_id: int) -> Contract | None:
        """查询指定 ID 的合同，不存在时返回 None。"""
        return self.repository.get_by_id(contract_id)

    def list_customer_contracts(self, customer_id: int) -> list[Contract]:
        """返回指定客户的全部合同，无匹配结果时返回空列表。"""
        return self.repository.list_by_customer(customer_id)

    def list_expiring_contracts(
        self,
        customer_id: int,
        days: int = 30,
        on_date: date | None = None,
    ) -> list[Contract]:
        """返回客户在指定日期有效且剩余 0 到 days 天（含两端）的合同。

        on_date 为 None 时使用当天；days 为负数时抛出 ValueError。
        """
        if days < 0:
            raise ValueError("days 不能小于 0")

        if on_date is None:
            on_date = date.today()

        contracts = self.repository.list_by_customer(customer_id)
        return [
            contract
            for contract in contracts
            if contract.is_expiring_soon(days=days, on_date=on_date)
        ]
