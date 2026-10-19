def test_home_page_shows_refund_policy_notice(client):
    res = client.get("/")
    assert res.status_code == 200
    assert "Refunds can be requested within 30 days of purchase" in res.text
