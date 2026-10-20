def test_create_and_get_order(client, make_customer):
    cid = make_customer()
    res = client.post("/orders", json={"customer_id": cid, "total_amount": 50_000})
    assert res.status_code == 201
    order = res.json()
    assert order["status"] == "PAID"
    assert order["ordered_at"] == "2026-10-16"
    assert client.get(f"/orders/{order['id']}").json()["total_amount"] == 50_000


def test_create_order_for_unknown_customer_returns_404(client):
    res = client.post("/orders", json={"customer_id": 999, "total_amount": 1_000})
    assert res.status_code == 404


def test_get_unknown_order_returns_404(client):
    assert client.get("/orders/12345").status_code == 404


def test_list_customer_orders_newest_first(client, make_customer, make_order):
    cid = make_customer()
    make_order(cid, days_ago=10)
    make_order(cid, days_ago=2)
    orders = client.get(f"/customers/{cid}/orders").json()
    assert [o["ordered_at"] for o in orders] == ["2026-10-14", "2026-10-06"]
