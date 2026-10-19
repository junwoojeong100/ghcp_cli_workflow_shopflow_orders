"""Refund policy rules. When the policy changes, check this module first."""

from datetime import date

REFUND_WINDOW_DAYS = 30


class RefundDenied(Exception):
    """Raised when a refund cannot be processed under the refund policy."""

    def __init__(self, code: str, message: str):
        super().__init__(message)
        self.code = code
        self.message = message


def days_since(ordered_at: str, today: date) -> int:
    return (today - date.fromisoformat(ordered_at[:10])).days


def check_refund_window(ordered_at: str, today: date) -> None:
    if days_since(ordered_at, today) > REFUND_WINDOW_DAYS:
        raise RefundDenied(
            "WINDOW_EXPIRED", f"The refund period ({REFUND_WINDOW_DAYS} days) has passed."
        )


def check_amount(order_total: int, already_refunded: int, amount: int) -> None:
    if already_refunded + amount > order_total:
        raise RefundDenied("AMOUNT_EXCEEDED", "The refund amount exceeds the order amount.")
