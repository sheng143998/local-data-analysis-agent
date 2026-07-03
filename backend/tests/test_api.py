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
    assert body["path"] in {"cold_path", "fast_path"}
    assert "orders" in body["sql"]
    assert "SQL Guard" in body["source"]["security"]
    assert "销售额" in body["source"]["metricDefinition"]
    assert "检索 SQL Memory" in [step["name"] for step in body["steps"]]
    assert "召回指标口径" in [step["name"] for step in body["steps"]]
    assert body["trace"]["toolCalls"] == 8
    assert len(body["rows"]) == 30
    assert body["steps"][-1]["status"] == "已完成"
    assert "真实 PostgreSQL 数据" in body["summary"]


def test_analyze_supports_monthly_order_count_slice() -> None:
    response = client.post("/api/analyze", json={"question": "最近 90 天每月订单数是多少？"})

    assert response.status_code == 200
    body = response.json()
    assert body["path"] in {"cold_path", "fast_path", "rewrite_path"}
    assert "DATE_TRUNC('MONTH'" in body["sql"].upper()
    assert "COUNT(DISTINCT o.id) AS order_count" in body["sql"]
    assert len(body["rows"]) <= 3
    assert "订单数" in body["summary"]
    assert "月份" in body["summary"]
