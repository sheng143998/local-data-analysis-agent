"""查询结果缓存服务与缓存 Key 构造器测试。"""
from time import perf_counter
from unittest.mock import patch

from backend.app.agents.analysis_graph import _execute_sql_node, _explain_sql_node
from backend.app.schemas.sql_execution import SqlExecutionResult, SqlExplainResult
from backend.app.schemas.sql_validation import SqlGuardResult
from backend.app.services.cache_key_builder import build_query_cache_key
from backend.app.services.cache_service import CacheService


def _cache(prefix: str = "test") -> CacheService:
    return CacheService(redis_url="", prefix=prefix, default_ttl=60, max_entries=8)


def _guard(sql: str = "SELECT 1") -> SqlGuardResult:
    return SqlGuardResult(allowed=True, final_sql=sql)


def _state(sql: str = "SELECT 1", query_plan: dict | None = None) -> dict:
    return {
        "guard": _guard(sql),
        "question_intent": {
            "query_plan": query_plan or {"metric": "sales"},
            "resolved_contracts": [{"contract_key": "sales", "version": 1}],
        },
        "app_user_id": None,
        "selected_sql": sql,
        "started": perf_counter(),
        "node_timings": {},
    }


def test_cache_service_set_get_delete_prefix() -> None:
    cache = _cache()
    cache.set("a", {"value": 1})
    cache.set("b", {"value": 2})
    assert cache.get("a") == {"value": 1}
    assert cache.get("b") == {"value": 2}

    deleted = cache.delete_prefix("a")
    assert deleted >= 1
    assert cache.get("a") is None
    assert cache.get("b") == {"value": 2}

    assert cache.clear_all() >= 1
    assert cache.get("b") is None


def test_cache_service_lru_eviction() -> None:
    cache = _cache()
    for index in range(10):
        cache.set(f"key-{index}", {"index": index})
    # max_entries=8，最早写入的两条应被淘汰。
    assert cache.get("key-0") is None
    assert cache.get("key-1") is None
    assert cache.get("key-9") == {"index": 9}


def test_cache_key_builder_stable_and_sensitive() -> None:
    query_plan = {"metric": "sales", "dimension": "day"}
    key1 = build_query_cache_key(final_sql="SELECT 1", query_plan=query_plan, app_user_id=None)
    key2 = build_query_cache_key(final_sql="SELECT 1", query_plan=query_plan, app_user_id=None)
    assert key1 == key2

    assert key1 != build_query_cache_key(final_sql="SELECT 2", query_plan=query_plan, app_user_id=None)
    assert key1 != build_query_cache_key(final_sql="SELECT 1", query_plan={"metric": "orders"}, app_user_id=None)
    assert key1 != build_query_cache_key(final_sql="SELECT 1", query_plan=query_plan, app_user_id="user-a")
    assert key1 != build_query_cache_key(
        final_sql="SELECT 1",
        query_plan=query_plan,
        resolved_contracts=[{"contract_key": "orders", "version": 2}],
    )


def test_explain_node_hits_cache_and_skips_execution() -> None:
    cache = _cache("hit")
    state = _state()
    key = build_query_cache_key(
        final_sql="SELECT 1",
        query_plan=state["question_intent"]["query_plan"],
        app_user_id=None,
        resolved_contracts=state["question_intent"]["resolved_contracts"],
    )
    cache.set(
        key,
        {
            "execution": SqlExecutionResult(
                status="success",
                columns=["?column?"],
                rows=[{"?column?": 1}],
                row_count=1,
                latency_ms=3,
            ).model_dump(mode="json")
        },
    )

    with patch("backend.app.agents.analysis_graph.get_cache_service", return_value=cache):
        explained = _explain_sql_node(dict(state))
        assert explained["cache_hit"] is True
        assert explained["explain"].status == "success"
        assert explained["execution"].row_count == 1

        with patch(
            "backend.app.agents.analysis_graph.execute_guarded_sql",
            side_effect=AssertionError("缓存命中时不应执行数据库"),
        ):
            executed = _execute_sql_node({**state, **explained, "started": perf_counter()})
            assert executed["execution"].row_count == 1


def test_execute_node_writes_cache_on_success() -> None:
    cache = _cache("write")
    state = _state()
    key = build_query_cache_key(
        final_sql="SELECT 1",
        query_plan=state["question_intent"]["query_plan"],
        app_user_id=None,
        resolved_contracts=state["question_intent"]["resolved_contracts"],
    )
    state["cache_key"] = key
    state["cache_hit"] = False

    with (
        patch("backend.app.agents.analysis_graph.get_cache_service", return_value=cache),
        patch(
            "backend.app.agents.analysis_graph.execute_guarded_sql",
            return_value=SqlExecutionResult(
                status="success",
                columns=["?column?"],
                rows=[{"?column?": 1}],
                row_count=1,
                latency_ms=2,
            ),
        ),
    ):
        executed = _execute_sql_node(dict(state))
        assert executed["execution"].status == "success"

    cached = cache.get(key)
    assert cached is not None
    assert cached["execution"]["row_count"] == 1
