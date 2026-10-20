def test_home_page_shows_refund_policy_notice(client):
    res = client.get("/")
    assert res.status_code == 200
    assert "환불은 구매 후 30일 이내" in res.text
