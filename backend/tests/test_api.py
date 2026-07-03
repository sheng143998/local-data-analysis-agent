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
    assert body["path"] == "cold_path"
    assert "orders" in body["sql"]
    assert "SQL Guard" in body["source"]["security"]
    assert len(body["rows"]) == 30
    assert body["steps"][-1]["status"] == "已完成"
    assert "真实 PostgreSQL 数据" in body["summary"]
