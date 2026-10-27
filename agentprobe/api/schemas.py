"""合同 API 的响应模型。"""

from datetime import date
from decimal import Decimal

from pydantic import BaseModel, ConfigDict


class ContractRead(BaseModel):
    """定义合同查询的响应字段，支持从领域对象的属性读取数据。"""

    model_config = ConfigDict(from_attributes=True)

    id: int
    customer_id: int
    name: str
    amount: Decimal
    start_date: date
    end_date: date
    status: str
