from dataclasses import dataclass
from datetime import date
from decimal import Decimal


@dataclass
class Contract:
    id: int  # 合同id
    customer_id: int
    name: str  # 合同名称
    amount: Decimal  # 合同金额
    start_date: date  # 合同开始日期
    end_date: date  # 合同结束日期
    status: str  # 合同状态

    def __post_init__(self) -> None:
        if self.start_date > self.end_date:  # 如果开始日期大于结束日期，则抛出异常
            raise ValueError("start_date 不能大于 end_date")  # 开始日期不能大于结束日期
        if self.status not in [
            "active",
            "pending",
            "expired",
            "cancelled",
        ]:  # 如果合同状态不是 active, pending, expired, cancelled，则抛出异常
            raise ValueError(
                "status 只能是 active, pending, expired, cancelled"
            )  # 合同状态只能是 active, pending, expired, cancelled
        if self.amount < 0:  # 如果合同金额小于0，则抛出异常
            raise ValueError("amount 不能小于 0")  # 合同金额不能小于0

    def is_active(self, on_date: date | None = None) -> bool:
        """判断合同在指定日期是否有效。

        合同必须处于 active 状态，且判断日期位于合同有效期内。
        """
        if on_date is None:  # 如果判断日期为空，则使用当前日期
            on_date = date.today()  # 使用当前日期
        return (
            self.status == "active" and self.start_date <= on_date <= self.end_date
        )  # 判断合同是否有效

    def is_expiring_soon(
        self,
        days: int = 30,  # 到期前多少天提醒
        on_date: date | None = None,  # 判断日期
    ) -> bool:
        """判断合同在指定日期是否即将到期。

        合同必须处于 active 状态，且判断日期距离合同结束日期不超过指定天数。
        """
        if days < 0:  # 如果到期前多少天提醒小于0，则抛出异常
            raise ValueError("days 不能小于 0")  # 到期前多少天提醒不能小于0

        if on_date is None:  # 如果判断日期为空，则使用当前日期
            on_date = date.today()  # 使用当前日期

        remaining_days = (self.end_date - on_date).days  # 计算剩余天数
        return (
            self.is_active(on_date) and 0 <= remaining_days <= days
        )  # 判断合同是否即将到期
