"""FastAPI 应用入口与服务装配。"""

from fastapi import FastAPI

from agentprobe.repositories.memory_contract_repository import (
    InMemoryContractRepository,
)
from agentprobe.repositories.protocol import ContractRepository
from agentprobe.services.contract_service import ContractService


def create_app(repository: ContractRepository | None = None) -> FastAPI:
    """创建应用，每个应用复用自己的仓储，也允许外部传入测试仓储。"""
    if repository is None:
        repository = InMemoryContractRepository()

    app = FastAPI(title="AgentProbe")
    app.state.contract_service = ContractService(repository)

    @app.get("/health")
    def health() -> dict[str, str]:
        """返回应用健康状态。"""
        return {"status": "ok"}

    return app


app = create_app()
