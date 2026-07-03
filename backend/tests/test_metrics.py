from fastapi.testclient import TestClient
from uuid import uuid4

from backend.app.main import app


client = TestClient(app)


def test_metric_crud_flow() -> None:
    metric_name = f"gross_margin_rate_test_{uuid4().hex[:8]}"
    list_response = client.get("/api/metrics")
    assert list_response.status_code == 200
    assert len(list_response.json()) >= 1

    create_response = client.post(
        "/api/metrics",
        json={
            "metric_name": metric_name,
            "display_name": "测试毛利率",
            "description": "测试用毛利率指标",
            "formula": "(sales - cost) / sales",
            "required_tables": ["orders", "product_costs"],
            "required_fields": ["orders.total_amount", "product_costs.cost"],
            "default_filters": {},
            "example_question": "哪个品类毛利率最高？",
            "owner": "测试分析组",
            "status": "draft",
        },
    )
    assert create_response.status_code == 200
    metric = create_response.json()
    metric_id = metric["id"]

    update_response = client.put(
        f"/api/metrics/{metric_id}",
        json={"status": "enabled", "display_name": "毛利率"},
    )
    assert update_response.status_code == 200
    assert update_response.json()["status"] == "enabled"
    assert update_response.json()["display_name"] == "毛利率"

    get_response = client.get(f"/api/metrics/{metric_id}")
    assert get_response.status_code == 200
    assert get_response.json()["metric_name"] == metric_name

    delete_response = client.delete(f"/api/metrics/{metric_id}")
    assert delete_response.status_code == 200
    assert delete_response.json()["deleted"] is True

    missing_response = client.get(f"/api/metrics/{metric_id}")
    assert missing_response.status_code == 404
