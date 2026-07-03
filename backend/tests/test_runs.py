from fastapi.testclient import TestClient

from backend.app.main import app


client = TestClient(app)


def test_analyze_writes_query_run_and_tool_calls() -> None:
    question = "最近 30 天销售额按天变化如何？"
    analyze_response = client.post("/api/analyze", json={"question": question})
    assert analyze_response.status_code == 200

    list_response = client.get("/api/runs?limit=1")
    assert list_response.status_code == 200
    runs = list_response.json()
    assert len(runs) == 1
    latest_run = runs[0]
    assert latest_run["user_question"] == question
    assert latest_run["guard_status"] == "allowed"
    assert latest_run["execution_status"] == "success"
    assert latest_run["row_count"] == 30
    assert latest_run["memory_hit"] in {True, False}
    assert "orders" in latest_run["final_sql"]

    detail_response = client.get(f"/api/runs/{latest_run['id']}")
    assert detail_response.status_code == 200
    detail = detail_response.json()
    tool_names = {tool_call["tool_name"] for tool_call in detail["tool_calls"]}
    assert "context_builder.build_retrieval_context" in tool_names
    assert "sql_memory_tools.retrieve_sql_memory" in tool_names
    assert "sql_memory_tools.plan_sql_reuse" in tool_names
    assert "sql_validation_tools.guard_sql" in tool_names
    assert "sql_execution_tools.execute_guarded_sql" in tool_names
    assert "analysis_presenter.present_sales_trend_result" in tool_names
    assert "sql_memory_tools.upsert_successful_sql_memory" in tool_names

    memory_response = client.get("/api/memories?limit=1")
    assert memory_response.status_code == 200
    memories = memory_response.json()
    assert len(memories) >= 1
    assert "orders" in memories[0]["tables"]


def test_get_missing_run_returns_404() -> None:
    response = client.get("/api/runs/00000000-0000-0000-0000-000000000000")
    assert response.status_code == 404


def test_get_missing_memory_returns_404() -> None:
    response = client.get("/api/memories/00000000-0000-0000-0000-000000000000")
    assert response.status_code == 404
