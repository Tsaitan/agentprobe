"""协调合同查询和领域规则的业务服务。"""

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
