"""协调合同查询和领域规则的业务服务。"""

from agentprobe.repositories.memory_contract_repository import (
    InMemoryContractRepository,
)


class ContractService:
    """使用外部传入的仓储组织合同业务操作。"""

    def __init__(self, repository: InMemoryContractRepository) -> None:
        self.repository = repository
