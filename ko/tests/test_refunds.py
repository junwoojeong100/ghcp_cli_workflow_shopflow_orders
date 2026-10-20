import json


def refund(client, order_id, amount):
    return client.post(f"/orders/{order_id}/refund", json={"amount": amount})


def test_refund_within_window_is_auto_approved(client, make_customer, make_order):
    order = make_order(make_customer(), amount=80_000, days_ago=10)
    res = refund(client, order, 80_000)
    assert res.status_code == 201
    assert res.json()["status"] == "APPROVED"


def test_refund_on_day_30_is_allowed(client, make_customer, make_order):
    order = make_order(make_customer(), days_ago=30)
    assert refund(client, order, 10_000).status_code == 201


def test_refund_on_day_31_is_rejected(client, make_customer, make_order):
    order = make_order(make_customer(), days_ago=31)
    res = refund(client, order, 10_000)
    assert res.status_code == 400
    assert res.json()["detail"]["code"] == "WINDOW_EXPIRED"


def test_refund_amount_over_order_total_is_rejected(client, make_customer, make_order):
    order = make_order(make_customer(), amount=50_000)
    res = refund(client, order, 50_001)
    assert res.status_code == 400
    assert res.json()["detail"]["code"] == "AMOUNT_EXCEEDED"


def test_partial_refunds_cannot_exceed_total(client, make_customer, make_order):
    order = make_order(make_customer(), amount=100_000)
    assert refund(client, order, 60_000).status_code == 201
    res = refund(client, order, 60_000)
    assert res.status_code == 400
    assert res.json()["detail"]["code"] == "AMOUNT_EXCEEDED"


def test_cancelled_order_cannot_be_refunded(client, make_customer, make_order):
    order = make_order(make_customer(), status="CANCELLED")
    res = refund(client, order, 10_000)
    assert res.json()["detail"]["code"] == "ORDER_CANCELLED"


def test_shipped_order_refund_waits_for_manual_approval(client, make_customer, make_order, query):
    order = make_order(make_customer(), days_ago=2, status="SHIPPED")
    res = refund(client, order, 10_000)
    assert res.json()["status"] == "REQUESTED"
    assert query("SELECT * FROM notifications") == []


def test_admin_approves_requested_refund_and_customer_is_notified(
    client, make_customer, make_order, admin_headers, query
):
    order = make_order(make_customer(), days_ago=2, status="SHIPPED")
    rid = refund(client, order, 10_000).json()["id"]
    res = client.post(f"/admin/refunds/{rid}/approve", headers=admin_headers)
    assert res.status_code == 200
    assert res.json()["status"] == "APPROVED"
    assert len(query("SELECT * FROM notifications")) == 1


def test_admin_rejects_requested_refund(client, make_customer, make_order, admin_headers):
    order = make_order(make_customer(), days_ago=2, status="SHIPPED")
    rid = refund(client, order, 10_000).json()["id"]
    res = client.post(f"/admin/refunds/{rid}/reject", headers=admin_headers)
    assert res.json()["status"] == "REJECTED"


def test_admin_endpoints_require_token(client):
    assert client.get("/admin/refunds").status_code == 401
    assert client.post("/admin/refunds/1/approve").status_code == 401


def test_only_pending_refunds_can_be_decided(client, make_customer, make_order, admin_headers):
    order = make_order(make_customer(), days_ago=1)
    rid = refund(client, order, 10_000).json()["id"]
    res = client.post(f"/admin/refunds/{rid}/approve", headers=admin_headers)
    assert res.status_code == 400
    assert res.json()["detail"]["code"] == "NOT_PENDING"


def test_refund_request_is_written_to_audit_log(client, make_customer, make_order, query):
    order = make_order(make_customer(), amount=30_000)
    refund(client, order, 30_000)
    rows = query("SELECT actor, action, detail FROM audit_log")
    assert rows[0]["action"] == "refund.requested"
    assert json.loads(rows[0]["detail"])["amount"] == 30_000


def test_approved_refund_email_mentions_refund_window(client, make_customer, make_order, query):
    order = make_order(make_customer(), amount=30_000)
    refund(client, order, 30_000)
    body = query("SELECT body FROM notifications")[0]["body"]
    assert "30일" in body


def test_unknown_order_returns_404(client):
    assert refund(client, 424242, 1_000).status_code == 404
