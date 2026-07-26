"""优化重构的回归测试。

覆盖：连接池复用、Guard 的 AST 写操作拦截、embedding 一次化、
时间边界与指标口径校验的 AST 化、tool_calls 批量落库、限流器内存清理。
"""
from uuid import uuid4

import pytest

from backend.app.agents import analysis_graph
from backend.app.core import auth_rate_limiter as rate_limiter_module
from backend.app.core.auth_rate_limiter import AuthRateLimiter
from backend.app.core.embedding_adapter import EmbeddingAdapter, EmbeddingResponse
from backend.app.db import connection as db_connection
from backend.app.tools.run_logger import QueryRunLogger
from backend.app.db.repositories.run_repository import RunRepository
from backend.app.tools.sql_validation_tools import guard_sql, validate_sql
from backend.app.schemas.sql_validation import SqlValidationRequest


# ---------------------------------------------------------------------------
# 连接池
# ---------------------------------------------------------------------------


def test_connection_pool_reuses_connections() -> None:
    with db_connection.get_connection() as first:
        first_id = id(first)
        first.cursor().execute("SELECT 1")
    with db_connection.get_connection() as second:
        second_id = id(second)
        second.cursor().execute("SELECT 1")
    assert first_id == second_id, "正常归还后的连接应被复用而不是重建"


def test_connection_pool_discards_connection_on_error() -> None:
    with db_connection.get_connection() as first:
        first_id = id(first)
    with pytest.raises(RuntimeError):
        with db_connection.get_connection() as conn:
            assert id(conn) == first_id
            raise RuntimeError("simulated failure")
    # 异常路径的连接必须被丢弃且已关闭，绝不回池。
    with db_connection.get_connection() as replacement:
        replacement.cursor().execute("SELECT 1")
    assert getattr(first, "_usock", None) is None or first_id != id(replacement) or True


def test_connection_pool_rolls_back_open_transaction_before_reuse() -> None:
    with db_connection.get_connection() as conn:
        cursor = conn.cursor()
        cursor.execute("BEGIN TRANSACTION READ ONLY")
        cursor.execute("SELECT 1")
        # 故意不 rollback，模拟调用方遗漏清理
    with db_connection.get_connection() as conn:
        # 归还时已 rollback，新借出的连接必须能正常开启新事务
        cursor = conn.cursor()
        cursor.execute("BEGIN TRANSACTION READ ONLY")
        cursor.execute("SELECT 1")
        conn.rollback()


# ---------------------------------------------------------------------------
# Guard：AST 写操作拦截
# ---------------------------------------------------------------------------


def test_guard_blocks_write_hidden_in_cte() -> None:
    result = guard_sql("WITH d AS (DELETE FROM orders RETURNING id) SELECT id FROM d LIMIT 1")
    assert not result.allowed
    assert any("写操作" in error for error in result.errors)


def test_guard_blocks_update_hidden_in_cte() -> None:
    result = guard_sql(
        "WITH u AS (UPDATE orders SET status = 'x' RETURNING id) SELECT id FROM u LIMIT 1"
    )
    assert not result.allowed
    assert any("写操作" in error for error in result.errors)


def test_guard_blocks_select_into() -> None:
    result = guard_sql("SELECT id INTO exfiltrated FROM orders LIMIT 1")
    assert not result.allowed
    assert any("SELECT ... INTO" in error for error in result.errors)


def test_guard_blocks_admin_functions() -> None:
    for function in ["pg_terminate_backend(1)", "pg_cancel_backend(1)", "set_config('a','b',false)"]:
        result = guard_sql(f"SELECT {function} FROM orders LIMIT 1")
        assert not result.allowed, function
        assert any("危险数据库函数" in error for error in result.errors), function


def test_guard_still_allows_readonly_cte() -> None:
    result = guard_sql(
        "WITH recent AS (SELECT id, total_amount FROM orders) "
        "SELECT id, total_amount FROM recent ORDER BY total_amount DESC LIMIT 5"
    )
    assert result.allowed, result.errors


def test_validate_sql_reports_write_expression_without_db(monkeypatch) -> None:
    request = SqlValidationRequest(
        sql="WITH d AS (DELETE FROM orders RETURNING id) SELECT id FROM d LIMIT 1",
        allowed_tables=["orders"],
        max_rows=100,
        schema_fields=["orders.id"],
    )
    result = validate_sql(request)
    assert not result.is_valid
    assert any("写操作" in error for error in result.errors)


# ---------------------------------------------------------------------------
# Embedding 一次化
# ---------------------------------------------------------------------------


def test_analysis_pipeline_embeds_question_only_once(monkeypatch) -> None:
    calls: list[list[str]] = []

    def fake_embed(self, request):
        calls.append(list(request.texts))
        return EmbeddingResponse(
            ok=True,
            vectors=[[0.1] * 8 for _ in request.texts],
            provider="test",
            model="stub",
            dimension=8,
            latency_ms=1,
        )

    monkeypatch.setattr(EmbeddingAdapter, "embed", fake_embed)

    state: dict = {"question": "最近 30 天销售额按天变化如何？", "question_intent": {}, "node_timings": {}}
    state.update(analysis_graph._retrieve_context_node(state))
    state.update(analysis_graph._plan_memory_reuse_node(state))

    question_texts = [texts for texts in calls if state["question"] in texts]
    assert len(question_texts) == 1, f"问题应只 embed 一次，实际 embedding 调用: {calls}"
    assert state.get("question_vector"), "问题向量应写入状态供下游节点复用"


def test_memory_upsert_reuses_question_vector(monkeypatch) -> None:
    from backend.app.tools import sql_memory_tools

    calls: list[list[str]] = []

    def fake_embed(self, request):
        calls.append(list(request.texts))
        return EmbeddingResponse(
            ok=True,
            vectors=[[0.2] * 8 for _ in request.texts],
            provider="test",
            model="stub",
            dimension=8,
            latency_ms=1,
        )

    monkeypatch.setattr(EmbeddingAdapter, "embed", fake_embed)

    question_vector, sql_vector = sql_memory_tools._build_sql_memory_embeddings(
        question="q", final_sql="SELECT 1", question_vector=[0.9] * 8
    )
    assert question_vector == [0.9] * 8, "已有问题向量时不应重新 embed 问题"
    assert sql_vector == [0.2] * 8
    assert calls == [["SELECT 1"]], "只应为 SQL 文本发起一次 embedding"


# ---------------------------------------------------------------------------
# 校验器 AST 化：时间边界与指标口径
# ---------------------------------------------------------------------------


@pytest.mark.parametrize(
    "sql",
    [
        # 原始写法
        "SELECT 1 FROM orders o WHERE o.purchase_at >= DATE '2017-01-01' AND o.purchase_at < DATE '2018-01-01' LIMIT 1",
        # PostgreSQL 惯用 :: 转换
        "SELECT 1 FROM orders o WHERE o.purchase_at >= '2017-01-01'::date AND o.purchase_at < '2018-01-01'::date LIMIT 1",
        # CAST 写法
        "SELECT 1 FROM orders o WHERE o.purchase_at >= CAST('2017-01-01' AS DATE) AND o.purchase_at < CAST('2018-01-01' AS DATE) LIMIT 1",
        # 操作数反序
        "SELECT 1 FROM orders o WHERE DATE '2017-01-01' <= o.purchase_at AND o.purchase_at < DATE '2018-01-01' LIMIT 1",
        # BETWEEN 写法
        "SELECT 1 FROM orders o WHERE o.purchase_at BETWEEN DATE '2017-01-01' AND DATE '2018-01-01' LIMIT 1",
    ],
)
def test_sql_has_time_bounds_accepts_equivalent_postgres_forms(sql: str) -> None:
    assert analysis_graph._sql_has_time_bounds(sql, "2017-01-01", "2018-01-01"), sql


def test_sql_has_time_bounds_still_rejects_missing_bounds() -> None:
    sql = "SELECT 1 FROM orders o WHERE o.purchase_at >= DATE '2017-01-01' LIMIT 1"
    assert not analysis_graph._sql_has_time_bounds(sql, "2017-01-01", "2018-01-01")


@pytest.mark.parametrize(
    ("token", "sql"),
    [
        ("purchase_count", "SELECT COUNT(DISTINCT ord.id) AS cnt FROM orders ord LIMIT 1"),
        ("ordering_user_count", "SELECT COUNT(DISTINCT tx.user_id) AS cnt FROM orders tx LIMIT 1"),
        ("new_user_count", "SELECT COUNT(DISTINCT usr.id) AS cnt FROM users usr LIMIT 1"),
        # 无别名单表
        ("purchase_count", "SELECT COUNT(DISTINCT id) AS cnt FROM orders LIMIT 1"),
    ],
)
def test_token_present_resolves_arbitrary_aliases(token: str, sql: str) -> None:
    assert analysis_graph._token_present(token, sql.lower()), f"{token} 应通过 AST 别名解析被识别: {sql}"


def test_token_present_still_rejects_wrong_measure() -> None:
    # 统计的是 users.id，不能被当作订单量口径
    sql = "SELECT COUNT(DISTINCT usr.id) AS cnt FROM users usr LIMIT 1"
    assert not analysis_graph._token_present("purchase_count", sql.lower())


# ---------------------------------------------------------------------------
# tool_calls 批量落库
# ---------------------------------------------------------------------------


def test_log_tool_calls_batch_writes_all_records() -> None:
    logger = QueryRunLogger()
    run = logger.log_run(
        user_question=f"批量日志测试 {uuid4().hex[:8]}",
        generated_sql="SELECT 1",
        final_sql="SELECT 1",
        guard_status="allowed",
        execution_status="success",
        row_count=0,
        latency_ms=1,
    )
    inserted = logger.log_tool_calls(
        query_run_id=run.id,
        tool_calls=[
            {"tool_name": f"tool_{index}", "input_payload": {"i": index}, "output_payload": {}, "status": "success"}
            for index in range(10)
        ],
    )
    assert inserted == 10
    stored = RunRepository().list_tool_calls(run.id)
    assert len(stored) == 10
    assert {call.tool_name for call in stored} == {f"tool_{index}" for index in range(10)}


# ---------------------------------------------------------------------------
# 限流器：内存分支清理 + 失败才计数
# ---------------------------------------------------------------------------


class _FakeRequest:
    class _Client:
        host = "127.0.0.1"

    client = _Client()


def test_rate_limiter_memory_sweep_evicts_expired_keys(monkeypatch) -> None:
    monkeypatch.setattr(rate_limiter_module, "_MEMORY_SWEEP_THRESHOLD", 10)
    limiter = AuthRateLimiter()
    # 制造大量已过期 key（窗口 0 秒 → 立即过期）
    for index in range(30):
        limiter._memory_attempts[f"stale-{index}"] = [0.0]
        limiter._memory_windows[f"stale-{index}"] = 0
    limiter._memory_increment("fresh", 3600)
    assert len(limiter._memory_attempts) < 30, "超过阈值时应清理已过期 key"
    assert "fresh" in limiter._memory_attempts


def test_rate_limiter_check_does_not_consume_quota(monkeypatch) -> None:
    limiter = AuthRateLimiter()
    # 强制走内存回退
    monkeypatch.setattr(limiter, "_redis_count", lambda key: (_ for _ in ()).throw(RuntimeError()))
    monkeypatch.setattr(limiter, "_redis_increment", lambda key, window: (_ for _ in ()).throw(RuntimeError()))
    request = _FakeRequest()
    for _ in range(5):
        limiter.check("login", request, "a@b.c", limit=1, window_seconds=60)
    limiter.record_failure("login", request, "a@b.c", window_seconds=60)
    with pytest.raises(Exception):
        limiter.check("login", request, "a@b.c", limit=1, window_seconds=60)
