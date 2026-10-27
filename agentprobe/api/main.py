"""FastAPI 应用入口与服务装配。"""

from typing import Annotated

from fastapi import Depends, FastAPI, HTTPException, Path, Request

from agentprobe.api.schemas import ContractRead
from agentprobe.repositories.memory_contract_repository import (
    InMemoryContractRepository,
)
from agentprobe.repositories.protocol import ContractRepository
from agentprobe.services.contract_service import ContractService


def get_contract_service(request: Request) -> ContractService:
    """从当前请求所属的应用中获取已装配的合同服务。"""
    return request.app.state.contract_service


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

    @app.get("/contracts/{contract_id}", response_model=ContractRead)
    def get_contract(
        contract_id: Annotated[int, Path(gt=0)],
        service: Annotated[ContractService, Depends(get_contract_service)],
    ) -> ContractRead:
        """按正整数 ID 查询合同，不存在时返回 404。"""
        contract = service.get_contract(contract_id)
        if contract is None:
            raise HTTPException(status_code=404, detail="合同不存在")

        return ContractRead.model_validate(contract)

    return app


app = create_app()
