"""Customer notification (email) queue. A separate worker does the actual sending."""

from . import clock

REFUND_APPROVED_SUBJECT = "[ShopFlow] Your refund has been approved"
REFUND_APPROVED_BODY = (
    "Hello {name},\n"
    "Your refund of ₩{amount:,} for order #{order_id} has been approved. "
    "You will receive the money within 3 business days.\n\n"
    "Note: Refunds can be requested within 30 days of purchase.\n"
)

REFUND_REJECTED_SUBJECT = "[ShopFlow] Your refund request has been rejected"
REFUND_REJECTED_BODY = (
    "Hello {name},\n"
    "Your refund request for order #{order_id} has been rejected. "
    "Please contact customer support for details.\n\n"
    "Note: Refunds can be requested within 30 days of purchase.\n"
)


def queue_email(db, customer_id: int, subject: str, body: str) -> None:
    db.execute(
        "INSERT INTO notifications (at, customer_id, channel, subject, body)"
        " VALUES (?, ?, 'EMAIL', ?, ?)",
        (clock.now().isoformat(), customer_id, subject, body),
    )
