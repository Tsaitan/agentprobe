"""合同仓储的读取接口约定。"""

from typing import Protocol

from agentprobe.domain.contract import Contract


class ContractRepository(Protocol):
    """声明合同服务所需的仓储读取能力。"""

    def get_by_id(self, contract_id: int) -> Contract | None:
        """查询指定 ID 的合同，不存在时返回 None。"""
        ...

    def list_by_customer(self, customer_id: int) -> list[Contract]:
        """返回指定客户的全部合同，无匹配结果时返回空列表。"""
        ...
