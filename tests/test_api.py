def test_health(client):
    rv = client.get("/api/health")
    assert rv.status_code == 200
    assert rv.get_json()["status"] == "ok"
