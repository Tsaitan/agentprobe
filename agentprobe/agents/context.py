"""Agent 执行时使用的本地依赖上下文。"""

from dataclasses import dataclass

from agentprobe.services.contract_service import ContractService


@dataclass
class AgentContext:
    """保存外部传入的合同服务，供工具执行时使用。"""

    contract_service: ContractService
