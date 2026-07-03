from fastapi.testclient import TestClient

from backend.app.main import app


client = TestClient(app)


def test_health() -> None:
    response = client.get("/api/health")
    assert response.status_code == 200
    assert response.json()["ok"] is True


def test_analyze_minimal_loop() -> None:
    response = client.post("/api/analyze", json={"question": "最近 30 天销售额按天变化如何？"})
    assert response.status_code == 200
    body = response.json()
    assert body["path"] == "rewrite_path"
    assert "FROM orders o" in body["sql"]
    assert body["source"]["security"] == "只读 SELECT"
    assert len(body["rows"]) == 30
    assert body["steps"][-1]["status"] == "已完成"
