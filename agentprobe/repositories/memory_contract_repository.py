"""使用内存字典保存合同。"""

from agentprobe.domain.contract import Contract


class InMemoryContractRepository:
    """提供合同的内存存储能力。"""

    def __init__(self) -> None:
        self._contracts: dict[int, Contract] = {}

    def add(self, contract: Contract) -> None:
        """添加合同；ID 已存在时抛出 ValueError，保留原合同。"""
        if contract.id in self._contracts:
            raise ValueError(f"合同 ID {contract.id} 已存在")

        self._contracts[contract.id] = contract
