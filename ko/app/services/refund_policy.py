"""환불 정책 규칙. 정책이 바뀌면 이 모듈을 먼저 확인한다."""

from datetime import date

REFUND_WINDOW_DAYS = 30


class RefundDenied(Exception):
    """정책상 환불을 처리할 수 없을 때 발생한다."""

    def __init__(self, code: str, message: str):
        super().__init__(message)
        self.code = code
        self.message = message


def days_since(ordered_at: str, today: date) -> int:
    return (today - date.fromisoformat(ordered_at[:10])).days


def check_refund_window(ordered_at: str, today: date) -> None:
    if days_since(ordered_at, today) > REFUND_WINDOW_DAYS:
        raise RefundDenied(
            "WINDOW_EXPIRED", f"환불 가능 기간({REFUND_WINDOW_DAYS}일)이 지났습니다."
        )


def check_amount(order_total: int, already_refunded: int, amount: int) -> None:
    if already_refunded + amount > order_total:
        raise RefundDenied("AMOUNT_EXCEEDED", "환불 금액이 주문 금액을 초과합니다.")
