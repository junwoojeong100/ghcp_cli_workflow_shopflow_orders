def test_health_returns_ok(client):
    res = client.get("/health")
    assert res.status_code == 200
    assert res.json()["status"] == "ok"


def test_health_reports_version(client):
    assert client.get("/health").json()["version"]
