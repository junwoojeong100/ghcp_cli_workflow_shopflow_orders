"""환불 접수와 승인/반려 처리."""

from .. import audit, clock, notifications
from . import order_service
from .refund_policy import RefundDenied, check_amount, check_refund_window

ACTIVE_STATUSES = ("REQUESTED", "APPROVED")


def get_refund(db, refund_id: int) -> dict:
    row = db.execute(
        "SELECT id, order_id, amount, status, requested_at, decided_at FROM refunds WHERE id = ?",
        (refund_id,),
    ).fetchone()
    if row is None:
        raise order_service.NotFound(f"환불 {refund_id} 을(를) 찾을 수 없습니다.")
    return dict(row)


def list_refunds(db, status: str | None = None) -> list[dict]:
    sql = "SELECT id, order_id, amount, status, requested_at, decided_at FROM refunds"
    params: tuple = ()
    if status:
        sql += " WHERE status = ?"
        params = (status,)
    return [dict(r) for r in db.execute(sql + " ORDER BY id DESC", params).fetchall()]


def request_refund(db, order_id: int, amount: int, actor: str = "customer") -> dict:
    order = order_service.get_order(db, order_id)
    customer = order_service.get_customer(db, order["customer_id"])
    if order["status"] == "CANCELLED":
        raise RefundDenied("ORDER_CANCELLED", "취소된 주문은 환불할 수 없습니다.")
    check_refund_window(order["ordered_at"], clock.today())
    already = db.execute(
        "SELECT COALESCE(SUM(amount), 0) FROM refunds WHERE order_id = ? AND status IN (?, ?)",
        (order_id, *ACTIVE_STATUSES),
    ).fetchone()[0]
    check_amount(order["total_amount"], already, amount)

    # 배송 중인 주문은 물류 확인이 필요하므로 관리자가 수동으로 승인한다.
    status = "REQUESTED" if order["status"] == "SHIPPED" else "APPROVED"
    now = clock.now().isoformat()
    cur = db.execute(
        "INSERT INTO refunds (order_id, amount, status, requested_at, decided_at)"
        " VALUES (?, ?, ?, ?, ?)",
        (order_id, amount, status, now, now if status == "APPROVED" else None),
    )
    refund_id = cur.lastrowid
    audit.log(
        db,
        actor,
        "refund.requested",
        {"refund_id": refund_id, "order_id": order_id, "amount": amount, "status": status},
    )
    if status == "APPROVED":
        _notify(db, customer, order_id, amount, approved=True)
    return get_refund(db, refund_id)


def decide_refund(db, refund_id: int, approve: bool, actor: str = "admin") -> dict:
    refund = get_refund(db, refund_id)
    if refund["status"] != "REQUESTED":
        raise RefundDenied("NOT_PENDING", "승인 대기 중인 환불만 처리할 수 있습니다.")
    new_status = "APPROVED" if approve else "REJECTED"
    db.execute(
        "UPDATE refunds SET status = ?, decided_at = ? WHERE id = ?",
        (new_status, clock.now().isoformat(), refund_id),
    )
    order = order_service.get_order(db, refund["order_id"])
    customer = order_service.get_customer(db, order["customer_id"])
    audit.log(db, actor, f"refund.{new_status.lower()}", {"refund_id": refund_id})
    _notify(db, customer, order["id"], refund["amount"], approved=approve)
    return get_refund(db, refund_id)


def _notify(db, customer: dict, order_id: int, amount: int, approved: bool) -> None:
    if approved:
        subject, body = notifications.REFUND_APPROVED_SUBJECT, notifications.REFUND_APPROVED_BODY
    else:
        subject, body = notifications.REFUND_REJECTED_SUBJECT, notifications.REFUND_REJECTED_BODY
    notifications.queue_email(
        db,
        customer["id"],
        subject,
        body.format(name=customer["name"], order_id=order_id, amount=amount),
    )
