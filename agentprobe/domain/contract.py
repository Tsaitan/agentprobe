from dataclasses import dataclass
from datetime import date
from decimal import Decimal


@dataclass
class Contract:
    id: int
    customer_id: int
    name: str
    amount: Decimal
    start_date: date
    end_date: date
    status: str

    def __post_init__(self):
        if self.start_date > self.end_date:
            raise ValueError("start_date 不能大于 end_date")
        if self.status not in ["active", "pending", "expired", "cancelled"]:
            raise ValueError("status 只能是 active, pending, expired, cancelled")
        if self.amount < 0:
            raise ValueError("amount 不能小于 0")

    def is_active(self, on_date: date | None = None) -> bool:
        # TODO: 判断合同是否有效
        if on_date is None:
            on_date = date.today()
        return self.status == "active" and self.start_date <= on_date <= self.end_date

    def is_expiring_soon(
        self,
        days: int = 30,
        on_date: date | None = None,
    ) -> bool:
        # TODO: 判断合同是否即将到期
        if days < 0:
            raise ValueError("days 不能小于 0")
    
        if on_date is None:
            on_date = date.today()

        remaining_days = (self.end_date - on_date).days
        return self.is_active(on_date) and 0 <= remaining_days <= days
        