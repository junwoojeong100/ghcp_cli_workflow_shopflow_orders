"""Customer and order lookup/creation."""

from .. import clock
from ..schemas import OrderCreate


class NotFound(Exception):
    pass


def list_customers(db) -> list[dict]:
    rows = db.execute("SELECT id, name, email, tier FROM customers ORDER BY id").fetchall()
    return [dict(r) for r in rows]


def get_customer(db, customer_id: int) -> dict:
    row = db.execute(
        "SELECT id, name, email, tier FROM customers WHERE id = ?", (customer_id,)
    ).fetchone()
    if row is None:
        raise NotFound(f"Customer {customer_id} was not found.")
    return dict(row)


def list_orders(db, customer_id: int) -> list[dict]:
    rows = db.execute(
        "SELECT id, customer_id, total_amount, status, ordered_at FROM orders"
        " WHERE customer_id = ? ORDER BY ordered_at DESC, id DESC",
        (customer_id,),
    ).fetchall()
    return [dict(r) for r in rows]


def get_order(db, order_id: int) -> dict:
    row = db.execute(
        "SELECT id, customer_id, total_amount, status, ordered_at FROM orders WHERE id = ?",
        (order_id,),
    ).fetchone()
    if row is None:
        raise NotFound(f"Order {order_id} was not found.")
    return dict(row)


def create_order(db, data: OrderCreate) -> dict:
    get_customer(db, data.customer_id)
    ordered_at = data.ordered_at or clock.today().isoformat()
    cur = db.execute(
        "INSERT INTO orders (customer_id, total_amount, status, ordered_at) VALUES (?, ?, ?, ?)",
        (data.customer_id, data.total_amount, data.status, ordered_at),
    )
    return get_order(db, cur.lastrowid)
