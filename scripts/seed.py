"""Demo sample data. Dates are relative to the run date, so every run gives the same scenario."""

import sqlite3
import sys
from datetime import date, datetime, timedelta, timezone

# (id, name, email, tier) - some tier spellings are irregular (migrated legacy data).
CUSTOMERS = [
    (1, "Seoyun Han", "seoyun.han@example.com", "VIP"),
    (2, "Doyun Kim", "doyun.kim@example.com", "STANDARD"),
    (3, "Jihu Park", "jihu.park@example.com", "vip"),
    (4, "Seoyeon Lee", "seoyeon.lee@example.com", "STANDARD"),
    (5, "Minjun Choi", "minjun.choi@example.com", "VIP"),
    (6, "Haeun Jung", "haeun.jung@example.com", None),
    (7, "Yejun Kang", "yejun.kang@example.com", "STANDARD"),
    (8, "Sua Cho", "sua.cho@example.com", "VIP "),
    (9, "Jiho Yoon", "jiho.yoon@example.com", "STANDARD"),
    (10, "Yuna Jang", "yuna.jang@example.com", "VIP"),
    (11, "Dohyeon Lim", "dohyeon.lim@example.com", "STANDARD"),
    (12, "Harin Oh", "harin.oh@example.com", "VIP"),
]

# (order ID, customer ID, amount, days since purchase, status)
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

# (refund ID, order ID, amount, status, days since request, days since decision)
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
