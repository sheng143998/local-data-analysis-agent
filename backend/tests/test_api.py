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


def test_analyze_supports_top_product_sales_slice() -> None:
    response = client.post("/api/analyze", json={"question": "销售额最高的前 10 个商品是什么？"})

    assert response.status_code == 200
    body = response.json()
    assert "ORDER BY daily_sales DESC" in body["sql"]
    assert "order_items" in body["sql"]
    assert len(body["rows"]) == 10
    assert "商品" in body["summary"]


def test_analyze_supports_top_category_sales_slice() -> None:
    response = client.post("/api/analyze", json={"question": "哪个商品品类销售额最高？"})

    assert response.status_code == 200
    body = response.json()
    assert "category_label" in body["sql"]
    assert "products" in body["sql"]
    assert len(body["rows"]) <= 10
    assert "品类" in body["summary"]


def test_analyze_supports_category_refund_rate_slice() -> None:
    response = client.post("/api/analyze", json={"question": "哪个商品品类退款率最高？"})

    assert response.status_code == 200
    body = response.json()
    assert "refund_rate" in body["sql"]
    assert "ORDER BY refund_rate DESC" in body["sql"]
    assert len(body["rows"]) <= 10
    assert "退款率" in body["summary"]


def test_analyze_supports_payment_success_rate_slice() -> None:
    response = client.post("/api/analyze", json={"question": "每个支付方式的成功率是多少？"})

    assert response.status_code == 200
    body = response.json()
    assert "payment_method_label" in body["sql"]
    assert "success_rate" in body["sql"]
    assert len(body["rows"]) <= 20
    assert "支付成功率" in body["summary"]
