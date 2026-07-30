"""第二轮优化回归测试：记忆生命周期、记忆优先快路径、异步簿记、embedding 缓存、run_id。"""
from uuid import uuid4

from fastapi.testclient import TestClient

from backend.app.core import background
from backend.app.core.config import settings
from backend.app.core.embedding_adapter import EmbeddingAdapter, EmbeddingResponse
from backend.app.db.repositories.memory_repository import SqlMemoryRepository
from backend.app.main import app
from backend.app.schemas.memories import SqlMemoryUpsert
from backend.app.services.memory_fast_path import try_memory_fast_path
from backend.app.tools.text_normalization import normalize_question
from backend.app.tools import vector_retrieval


client = TestClient(app)


def _upsert(repo: SqlMemoryRepository, question: str, *, sql: str = "SELECT 1 AS one", columns: list[str] | None = None, fingerprints: dict | None = None):
    return repo.upsert_success(
        SqlMemoryUpsert(
            canonical_question=question,
            sql_template=sql,
            final_sql=sql,
            tables=["orders"],
            metrics=["order_count"],
            result_columns=columns or ["one"],
            row_count=1,
            latency_ms=10,
            filters={"context_fingerprints": fingerprints or {"schema": "f1", "semantic_contracts": "c1"}},
        )
    )


# ---------------------------------------------------------------------------
# 1a：自动可信状态机
# ---------------------------------------------------------------------------


def test_memory_auto_verifies_after_threshold_consecutive_stable_successes(monkeypatch) -> None:
    monkeypatch.setattr(settings, "memory_auto_verify_threshold", 3)
    repo = SqlMemoryRepository()
    question = f"生命周期测试 {uuid4().hex[:8]} 订单总数"

    first = _upsert(repo, question)
    assert first.trust_status != "verified"
    assert first.filters["auto_verify_streak"] == 1

    second = _upsert(repo, question)
    assert second.trust_status != "verified"
    assert second.filters["auto_verify_streak"] == 2

    third = _upsert(repo, question)
    assert third.trust_status == "verified"
    assert third.filters["auto_verified"] is True
    assert third.success_count == 3


def test_result_shape_drift_resets_streak(monkeypatch) -> None:
    monkeypatch.setattr(settings, "memory_auto_verify_threshold", 3)
    repo = SqlMemoryRepository()
    question = f"形状漂移测试 {uuid4().hex[:8]}"

    _upsert(repo, question, columns=["a"])
    _upsert(repo, question, columns=["a"])
    drifted = _upsert(repo, question, columns=["a", "b"])  # 第三次形状变化
    assert drifted.trust_status != "verified"
    assert drifted.filters["auto_verify_streak"] == 1


def test_fingerprint_drift_resets_streak(monkeypatch) -> None:
    monkeypatch.setattr(settings, "memory_auto_verify_threshold", 3)
    repo = SqlMemoryRepository()
    question = f"指纹漂移测试 {uuid4().hex[:8]}"

    _upsert(repo, question, fingerprints={"schema": "f1"})
    _upsert(repo, question, fingerprints={"schema": "f1"})
    drifted = _upsert(repo, question, fingerprints={"schema": "CHANGED"})
    assert drifted.trust_status != "verified"
    assert drifted.filters["auto_verify_streak"] == 1


def test_record_failure_demotes_verified_memory(monkeypatch) -> None:
    monkeypatch.setattr(settings, "memory_auto_verify_threshold", 1)
    repo = SqlMemoryRepository()
    question = f"降级测试 {uuid4().hex[:8]}"
    memory = _upsert(repo, question)
    assert memory.trust_status == "verified"

    demoted = repo.record_failure(memory.id, reason="schema_drift")
    assert demoted is not None
    assert demoted.trust_status == "reviewed"
    assert demoted.failure_count == memory.failure_count + 1
    assert demoted.filters["auto_verify_streak"] == 0
    assert demoted.filters["demoted_reason"] == "schema_drift"


def test_manual_terminal_states_are_not_auto_promoted(monkeypatch) -> None:
    monkeypatch.setattr(settings, "memory_auto_verify_threshold", 1)
    repo = SqlMemoryRepository()
    question = f"终态测试 {uuid4().hex[:8]}"
    memory = _upsert(repo, question)
    repo.update_trust_status(memory.id, "deprecated")

    after = _upsert(repo, question)
    assert after.trust_status == "deprecated", "人工弃用状态不允许被自动复活"


def test_upsert_is_race_safe_under_unique_index() -> None:
    """并发同题写入依赖唯一索引 + ON CONFLICT：只允许一行存在。"""
    import threading

    repo = SqlMemoryRepository()
    question = f"并发测试 {uuid4().hex[:8]}"
    errors: list[Exception] = []

    def worker() -> None:
        try:
            _upsert(repo, question)
        except Exception as exc:  # noqa: BLE001
            errors.append(exc)

    threads = [threading.Thread(target=worker) for _ in range(4)]
    for thread in threads:
        thread.start()
    for thread in threads:
        thread.join()
    assert not errors
    from backend.app.db.connection import get_connection

    with get_connection() as conn:
        cursor = conn.cursor()
        cursor.execute(
            "SELECT COUNT(*) FROM sql_memories WHERE normalized_question = %s",
            (normalize_question(question),),
        )
        assert cursor.fetchone()[0] == 1


# ---------------------------------------------------------------------------
# 2a：记忆优先快路径
# ---------------------------------------------------------------------------


def _seed_verified(repo: SqlMemoryRepository, question: str, sql: str):
    memory = _upsert(repo, question, sql=sql)
    return repo.update_trust_status(memory.id, "verified")


def test_fast_path_answers_verified_repeat_question_without_model(monkeypatch) -> None:
    monkeypatch.setattr(settings, "graph_memory_first", True)
    repo = SqlMemoryRepository()
    question = f"快路径测试 {uuid4().hex[:8]} 订单量"
    _seed_verified(repo, question, "SELECT COUNT(DISTINCT o.id) AS order_count FROM orders o LIMIT 10")

    response = try_memory_fast_path(question)
    assert response is not None
    assert response.path == "fast_path"
    assert response.run_id is not None
    assert "order_count" in response.sql
    assert response.rows, "快路径应返回真实执行结果"


def test_fast_path_skips_unverified_memory(monkeypatch) -> None:
    monkeypatch.setattr(settings, "graph_memory_first", True)
    repo = SqlMemoryRepository()
    question = f"未验证测试 {uuid4().hex[:8]}"
    _upsert(repo, question, sql="SELECT COUNT(*) AS c FROM orders LIMIT 1")

    assert try_memory_fast_path(question) is None


def test_fast_path_disabled_by_flag(monkeypatch) -> None:
    monkeypatch.setattr(settings, "graph_memory_first", False)
    repo = SqlMemoryRepository()
    question = f"开关测试 {uuid4().hex[:8]}"
    _seed_verified(repo, question, "SELECT 1 AS one")

    assert try_memory_fast_path(question) is None


def test_fast_path_failure_demotes_and_falls_back(monkeypatch) -> None:
    """记忆 SQL 因 schema 漂移执行失败：降级 + 回退（返回 None）。"""
    monkeypatch.setattr(settings, "graph_memory_first", True)
    repo = SqlMemoryRepository()
    question = f"漂移回退测试 {uuid4().hex[:8]}"
    seeded = _seed_verified(
        repo, question, "SELECT missing_column FROM orders LIMIT 1"  # guard 字段校验会拒绝
    )

    assert try_memory_fast_path(question) is None
    after = repo.get(seeded.id)
    assert after.trust_status == "reviewed"
    assert after.failure_count == seeded.failure_count + 1


def test_fast_path_end_to_end_via_api(monkeypatch) -> None:
    """端到端：已验证记忆命中时 /api/analyze 秒回，且完全不触发模型生成。"""
    monkeypatch.setattr(settings, "graph_memory_first", True)
    from backend.app.agents import analysis_graph

    def _forbidden_generation(**kwargs):  # noqa: ANN003
        raise AssertionError("fast path 命中时不应触发模型生成")

    monkeypatch.setattr(analysis_graph, "_select_generated_sql", _forbidden_generation)

    repo = SqlMemoryRepository()
    question = f"端到端快路径 {uuid4().hex[:8]} 订单总量"
    _seed_verified(repo, question, "SELECT COUNT(DISTINCT o.id) AS order_count FROM orders o LIMIT 10")

    response = client.post("/api/analyze", json={"question": question})
    assert response.status_code == 200
    body = response.json()
    assert body["path"] == "fast_path"
    assert body["run_id"]
    assert body["rows"]


# ---------------------------------------------------------------------------
# 1c：异步簿记
# ---------------------------------------------------------------------------


def test_async_bookkeeping_writes_run_after_response(monkeypatch) -> None:
    monkeypatch.setattr(settings, "bookkeeping_async", True)
    monkeypatch.setattr(settings, "graph_memory_first", False)

    response = client.post("/api/analyze", json={"question": "最近 30 天销售额按天变化如何？"})
    assert response.status_code in {200, 503}
    run_id = response.json().get("run_id") if response.status_code == 200 else None

    assert background.wait_for_idle(timeout=15), "后台簿记应在超时前完成"
    if run_id:
        detail = client.get(f"/api/runs/{run_id}")
        assert detail.status_code == 200
        assert detail.json()["tool_calls"], "异步簿记完成后 tool_calls 应已落库"


# ---------------------------------------------------------------------------
# 4c / 4d：embedding 缓存与 run_id
# ---------------------------------------------------------------------------


def test_embedding_cache_hits_for_repeated_question(monkeypatch) -> None:
    monkeypatch.setattr(settings, "embedding_cache_size", 16)
    vector_retrieval.clear_embedding_cache()
    calls: list[str] = []

    def fake_embed(self, request):
        calls.extend(request.texts)
        return EmbeddingResponse(
            ok=True, vectors=[[0.5] * 4 for _ in request.texts],
            provider="test", model="stub", dimension=4, latency_ms=1,
        )

    monkeypatch.setattr(EmbeddingAdapter, "embed", fake_embed)
    first = vector_retrieval.embed_question("重复问题缓存测试")
    second = vector_retrieval.embed_question("重复问题缓存测试")
    assert first == second
    assert len(calls) == 1, f"第二次应命中缓存，实际调用: {calls}"


def test_embedding_cache_disabled_when_size_zero(monkeypatch) -> None:
    monkeypatch.setattr(settings, "embedding_cache_size", 0)
    vector_retrieval.clear_embedding_cache()
    calls: list[str] = []

    def fake_embed(self, request):
        calls.extend(request.texts)
        return EmbeddingResponse(
            ok=True, vectors=[[0.5] * 4 for _ in request.texts],
            provider="test", model="stub", dimension=4, latency_ms=1,
        )

    monkeypatch.setattr(EmbeddingAdapter, "embed", fake_embed)
    vector_retrieval.embed_question("零缓存测试")
    vector_retrieval.embed_question("零缓存测试")
    assert len(calls) == 2


def test_analyze_response_carries_matching_run_id() -> None:
    response = client.post("/api/analyze", json={"question": "最近 30 天销售额按天变化如何？"})
    assert response.status_code == 200, response.json()
    run_id = response.json()["run_id"]
    assert run_id
    detail = client.get(f"/api/runs/{run_id}")
    assert detail.status_code == 200
    assert detail.json()["user_question"]
