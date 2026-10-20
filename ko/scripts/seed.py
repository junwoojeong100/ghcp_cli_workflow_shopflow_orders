"""시연용 샘플 데이터. 날짜는 실행 시점 기준 상대값이라 언제 실행해도 같은 시나리오가 된다."""

import sqlite3
import sys
from datetime import date, datetime, timedelta, timezone

# (id, 이름, 이메일, 등급) - 일부 등급 표기는 레거시 이관 데이터라 불규칙하다.
CUSTOMERS = [
    (1, "한서윤", "seoyun.han@example.com", "VIP"),
    (2, "김도윤", "doyun.kim@example.com", "STANDARD"),
    (3, "박지후", "jihu.park@example.com", "vip"),
    (4, "이서연", "seoyeon.lee@example.com", "STANDARD"),
    (5, "최민준", "minjun.choi@example.com", "VIP"),
    (6, "정하은", "haeun.jung@example.com", None),
    (7, "강예준", "yejun.kang@example.com", "STANDARD"),
    (8, "조수아", "sua.cho@example.com", "VIP "),
    (9, "윤지호", "jiho.yoon@example.com", "STANDARD"),
    (10, "장유나", "yuna.jang@example.com", "VIP"),
    (11, "임도현", "dohyeon.lim@example.com", "STANDARD"),
    (12, "오하린", "harin.oh@example.com", "VIP"),
]

# (주문ID, 고객ID, 금액, 구매 후 경과일, 상태)
ORDERS = [
    (1001, 1, 289_000, 45, "DELIVERED"),
    (1002, 1, 1_350_000, 12, "DELIVERED"),
    (1003, 2, 129_000, 45, "DELIVERED"),
    (1004, 2, 59_000, 10, "DELIVERED"),
    (1005, 3, 189_000, 50, "DELIVERED"),
    (1006, 4, 1_000_000, 5, "DELIVERED"),
    (1007, 4, 1_000_001, 6, "DELIVERED"),
    (1008, 5, 450_000, 61, "DELIVERED"),
    (1009, 5, 220_000, 60, "DELIVERED"),
    (1010, 6, 99_000, 40, "DELIVERED"),
    (1011, 7, 79_000, 30, "DELIVERED"),
    (1012, 7, 79_000, 31, "DELIVERED"),
    (1013, 8, 540_000, 35, "DELIVERED"),
    (1014, 9, 149_000, 2, "SHIPPED"),
    (1015, 10, 2_300_000, 20, "DELIVERED"),
    (1016, 11, 35_000, 7, "PAID"),
    (1017, 12, 810_000, 55, "DELIVERED"),
    (1018, 12, 64_000, 3, "CANCELLED"),
    (1019, 9, 55_000, 70, "DELIVERED"),
    (1020, 2, 99_000, 40, "DELIVERED"),
]

# (환불ID, 주문ID, 금액, 상태, 접수 경과일, 처리 경과일)
REFUNDS = [
    (1, 1019, 55_000, "APPROVED", 65, 65),
    (2, 1020, 99_000, "REJECTED", 38, 37),
]


def seed(db_path: str, today: date | None = None) -> None:
    today = today or datetime.now(timezone.utc).date()
    ts = datetime.combine(today, datetime.min.time(), tzinfo=timezone.utc).isoformat()
    conn = sqlite3.connect(db_path)
    for cid, name, email, tier in CUSTOMERS:
        conn.execute(
            "INSERT OR IGNORE INTO customers (id, name, email, tier, created_at)"
            " VALUES (?,?,?,?,?)",
            (cid, name, email, tier, ts),
        )
    for oid, cid, amount, days_ago, status in ORDERS:
        ordered_at = (today - timedelta(days=days_ago)).isoformat()
        conn.execute(
            "INSERT OR IGNORE INTO orders (id, customer_id, total_amount, status, ordered_at)"
            " VALUES (?,?,?,?,?)",
            (oid, cid, amount, status, ordered_at),
        )
    for rid, oid, amount, status, req_ago, dec_ago in REFUNDS:
        req = datetime.combine(today - timedelta(days=req_ago), datetime.min.time(), timezone.utc)
        dec = datetime.combine(today - timedelta(days=dec_ago), datetime.min.time(), timezone.utc)
        conn.execute(
            "INSERT OR IGNORE INTO refunds (id, order_id, amount, status, requested_at, decided_at)"
            " VALUES (?,?,?,?,?,?)",
            (rid, oid, amount, status, req.isoformat(), dec.isoformat()),
        )
    conn.commit()
    conn.close()


if __name__ == "__main__":
    target = sys.argv[1] if len(sys.argv) > 1 else "data/orders.db"
    seed(target)
    print(f"seeded: {target}")
