"""고객 알림(이메일) 발송 대기열. 실제 발송은 별도 워커가 담당한다."""

from . import clock

REFUND_APPROVED_SUBJECT = "[ShopFlow] 환불이 승인되었습니다"
REFUND_APPROVED_BODY = (
    "{name} 고객님, 안녕하세요.\n"
    "주문 #{order_id}의 환불 {amount:,}원이 승인되었습니다. 영업일 기준 3일 이내에 환급됩니다.\n\n"
    "※ 환불은 구매 후 30일 이내에 신청하실 수 있습니다.\n"
)

REFUND_REJECTED_SUBJECT = "[ShopFlow] 환불 요청이 반려되었습니다"
REFUND_REJECTED_BODY = (
    "{name} 고객님, 안녕하세요.\n"
    "주문 #{order_id}의 환불 요청이 반려되었습니다. 자세한 내용은 고객센터로 문의해 주세요.\n\n"
    "※ 환불은 구매 후 30일 이내에 신청하실 수 있습니다.\n"
)


def queue_email(db, customer_id: int, subject: str, body: str) -> None:
    db.execute(
        "INSERT INTO notifications (at, customer_id, channel, subject, body)"
        " VALUES (?, ?, 'EMAIL', ?, ?)",
        (clock.now().isoformat(), customer_id, subject, body),
    )
