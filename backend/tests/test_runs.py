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
    assert latest_run["rewritten_question"]
    assert latest_run["guard_status"] in {"allowed", "blocked"}
    assert latest_run["execution_status"] in {"success", "blocked"}
    assert latest_run["row_count"] >= 0
    assert latest_run["memory_hit"] in {True, False}
    if latest_run["final_sql"]:
        assert "orders" in latest_run["final_sql"]

    detail_response = client.get(f"/api/runs/{latest_run['id']}")
    assert detail_response.status_code == 200
    detail = detail_response.json()
    tool_calls = {tool_call["tool_name"]: tool_call for tool_call in detail["tool_calls"]}
    tool_names = set(tool_calls)
    assert "context_builder.build_retrieval_context" in tool_names
    assert "sql_memory_tools.retrieve_sql_memory" in tool_names
    assert "sql_memory_tools.plan_sql_reuse" in tool_names
    assert "sql_validation_tools.guard_sql" in tool_names
    assert "sql_execution_tools.execute_guarded_sql" in tool_names
    assert "analysis_presenter.present_sales_trend_result" in tool_names
    assert "sql_memory_tools.upsert_successful_sql_memory" in tool_names
    assert "analysis_graph.pipeline_timings" in tool_names

    context_payload = tool_calls["context_builder.build_retrieval_context"]["output_payload"]
    assert context_payload["metric_count"] >= 1
    assert context_payload["schema_column_count"] >= 1
    assert context_payload["relationship_count"] >= 0
    assert "orders" in context_payload["tables"]
    assert any(field.startswith("orders.") for field in context_payload["fields_sample"])

    generation_payload = tool_calls["analysis_graph.select_generated_sql"]["output_payload"]
    assert isinstance(generation_payload["has_sql"], bool)
    assert "generation_path" in generation_payload
    assert "warning_count" in generation_payload
    assert isinstance(generation_payload["warnings"], list)
    assert tool_calls["analysis_graph.select_generated_sql"]["latency_ms"] >= 0

    guard_payload = tool_calls["sql_validation_tools.guard_sql"]["output_payload"]
    assert guard_payload["guard_status"] in {"allowed", "blocked"}
    assert guard_payload["error_count"] >= 0
    assert isinstance(guard_payload["warnings"], list)

    timings_payload = tool_calls["analysis_graph.pipeline_timings"]["output_payload"]
    assert "node_timings_ms" in timings_payload
    assert timings_payload["total_latency_ms"] >= 0
    assert "slowest_node" in timings_payload

    debug_summary = detail["debug_summary"]
    assert debug_summary["run"]["id"] == latest_run["id"]
    assert debug_summary["run"]["question"] == question
    assert debug_summary["run"]["rewritten_question"] == latest_run["rewritten_question"]
    assert debug_summary["context"]["metric_count"] >= 1
    assert isinstance(debug_summary["sql_generation"]["has_sql"], bool)
    assert debug_summary["guard"]["status"] in {"allowed", "blocked"}
    assert debug_summary["execution"]["status"] in {"success", "blocked"}
    assert debug_summary["timings"]["total_latency_ms"] >= 0

    if latest_run["execution_status"] == "success":
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
