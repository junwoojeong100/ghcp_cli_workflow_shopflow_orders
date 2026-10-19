def test_customer_list_hides_email(client, make_customer):
    make_customer(name="Seoyun Han", tier="VIP", email="secret@example.com")
    body = client.get("/customers").json()
    assert body[0]["name"] == "Seoyun Han"
    assert "email" not in body[0]


def test_get_customer_returns_tier(client, make_customer):
    cid = make_customer(tier="VIP")
    assert client.get(f"/customers/{cid}").json()["tier"] == "VIP"


def test_unknown_customer_returns_404(client):
    assert client.get("/customers/999").status_code == 404
