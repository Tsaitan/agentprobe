"""合同查询的参数适配与结构化输出。"""

from datetime import date

from agentprobe.services.contract_service import ContractService


class InvalidToolArgumentsError(ValueError):
    """工具业务参数不合法，供后续 SDK 包装层识别。"""


def query_expiring_contracts(
    service: ContractService,
    customer_id: int,
    days: int = 30,
    on_date: str | None = None,
) -> dict[str, object]:
    """校验参数并查询即将到期合同，返回可序列化结果。

    customer_id 必须为正整数，days 必须为非负整数，均不接受布尔值。
    on_date 为 ISO 日期字符串，省略时使用当天；参数错误抛出
    InvalidToolArgumentsError，Service 执行异常原样向上传递。
    """
    if (
        not isinstance(customer_id, int)
        or isinstance(customer_id, bool)
        or customer_id <= 0
    ):
        raise InvalidToolArgumentsError("customer_id 必须是大于 0 的整数")
    if not isinstance(days, int) or isinstance(days, bool) or days < 0:
        raise InvalidToolArgumentsError("days 必须是大于等于 0 的整数")

    if on_date is None:
        effective_date = date.today()
    elif not isinstance(on_date, str):
        raise InvalidToolArgumentsError("on_date 必须是有效的 ISO 日期字符串或 None")
    else:
        try:
            effective_date = date.fromisoformat(on_date)
        except ValueError as error:
            raise InvalidToolArgumentsError(
                "on_date 必须是有效的 ISO 日期字符串或 None"
            ) from error

    contracts = service.list_expiring_contracts(
        customer_id=customer_id, days=days, on_date=effective_date
    )
    items = [
        {
            "id": contract.id,
            "name": contract.name,
            "end_date": contract.end_date.isoformat(),
            "amount": str(contract.amount),
        }
        for contract in contracts
    ]
    return {
        "ok": True,
        "customer_id": customer_id,
        "days": days,
        "on_date": effective_date.isoformat(),
        "count": len(items),
        "contracts": items,
    }
