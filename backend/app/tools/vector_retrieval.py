from __future__ import annotations

import logging
import threading
from collections import OrderedDict
from dataclasses import dataclass
from typing import Any, Literal

from backend.app.core.config import settings
from backend.app.core.embedding_adapter import EmbeddingAdapter, EmbeddingRequest
from backend.app.db.connection import get_connection


logger = logging.getLogger("backend.retrieval")

VectorTarget = Literal["metric", "schema"]


@dataclass(frozen=True)
class VectorCandidate:
    key: str
    score: float


_embedding_cache: "OrderedDict[tuple[str, str, str], list[float]]" = OrderedDict()
_embedding_cache_lock = threading.Lock()


def clear_embedding_cache() -> None:
    with _embedding_cache_lock:
        _embedding_cache.clear()


def embed_question(question: str, *, adapter: EmbeddingAdapter | None = None) -> list[float]:
    """把问题 embed 成向量；一次请求内应只调用一次，向量向下游检索复用。

    进程内 LRU（计划 4c）：重复问题（评测、仪表盘刷新、快路径回退）不再
    重复付远程 embedding 的延迟与费用；EMBEDDING_CACHE_SIZE=0 时禁用。
    """
    if not question.strip():
        return []
    active_adapter = adapter or EmbeddingAdapter()
    adapter_config = getattr(active_adapter, "config", None)
    if adapter_config is None:
        # 测试替身或自定义适配器没有标准配置：不参与缓存，直接调用。
        response = active_adapter.embed(EmbeddingRequest(texts=[question]))
        if not response.ok or not response.vectors:
            return []
        return response.vectors[0]
    cache_size = settings.embedding_cache_size
    cache_key = (
        adapter_config.provider,
        adapter_config.model,
        question.strip(),
    )
    if cache_size > 0:
        with _embedding_cache_lock:
            cached = _embedding_cache.get(cache_key)
            if cached is not None:
                _embedding_cache.move_to_end(cache_key)
                return list(cached)
    response = active_adapter.embed(EmbeddingRequest(texts=[question]))
    if not response.ok or not response.vectors:
        return []
    vector = response.vectors[0]
    if cache_size > 0:
        with _embedding_cache_lock:
            _embedding_cache[cache_key] = list(vector)
            _embedding_cache.move_to_end(cache_key)
            while len(_embedding_cache) > cache_size:
                _embedding_cache.popitem(last=False)
    return vector


def retrieve_metric_vector_candidates(
    question: str,
    *,
    limit: int = 8,
    adapter: EmbeddingAdapter | None = None,
    vector: list[float] | None = None,
) -> dict[str, float]:
    vector = vector if vector is not None else _embed_question(question, adapter=adapter)
    if not vector:
        return {}
    return _query_vector_candidates(
        target="metric",
        vector=vector,
        limit=limit,
    )


def retrieve_schema_vector_candidates(
    question: str,
    *,
    tables: list[str] | None = None,
    limit: int = 48,
    adapter: EmbeddingAdapter | None = None,
    vector: list[float] | None = None,
) -> dict[str, float]:
    vector = vector if vector is not None else _embed_question(question, adapter=adapter)
    if not vector:
        return {}
    return _query_vector_candidates(
        target="schema",
        vector=vector,
        limit=limit,
        tables=tables,
    )


def retrieve_sql_memory_vector_candidates(
    question: str,
    *,
    limit: int = 20,
    adapter: EmbeddingAdapter | None = None,
    vector: list[float] | None = None,
) -> dict[str, float]:
    vector = vector if vector is not None else _embed_question(question, adapter=adapter)
    if not vector:
        return {}
    return _query_sql_memory_vector_candidates(vector=vector, limit=limit)


def _embed_question(question: str, *, adapter: EmbeddingAdapter | None = None) -> list[float]:
    return embed_question(question, adapter=adapter)


def _query_vector_candidates(
    *,
    target: VectorTarget,
    vector: list[float],
    limit: int,
    tables: list[str] | None = None,
) -> dict[str, float]:
    try:
        with get_connection() as conn:
            cursor = conn.cursor()
            if target == "metric":
                rows = _query_metric_vectors(cursor, vector, limit)
            else:
                rows = _query_schema_vectors(cursor, vector, limit, tables or [])
    except Exception:
        # 静默降级会让"检索质量变差"无迹可查，至少留一条告警日志。
        logger.warning("vector retrieval degraded (target=%s)", target, exc_info=True)
        return {}

    return {
        str(key): _semantic_score(distance)
        for key, distance in rows
    }


def _query_metric_vectors(cursor: Any, vector: list[float], limit: int) -> list[tuple[str, float]]:
    cursor.execute(
        """
        SELECT metric_name, embedding <=> %s::vector AS distance
        FROM metric_definitions
        WHERE status = 'enabled' AND embedding IS NOT NULL
        ORDER BY embedding <=> %s::vector
        LIMIT %s
        """,
        (_vector_literal(vector), _vector_literal(vector), limit),
    )
    return cursor.fetchall()


def _query_schema_vectors(
    cursor: Any,
    vector: list[float],
    limit: int,
    tables: list[str],
) -> list[tuple[str, float]]:
    if tables:
        cursor.execute(
            """
            SELECT table_name || '.' || column_name AS field_name,
                   embedding <=> %s::vector AS distance
            FROM schema_metadata
            WHERE embedding IS NOT NULL AND table_name = ANY(%s)
            ORDER BY embedding <=> %s::vector
            LIMIT %s
            """,
            (_vector_literal(vector), tables, _vector_literal(vector), limit),
        )
    else:
        cursor.execute(
            """
            SELECT table_name || '.' || column_name AS field_name,
                   embedding <=> %s::vector AS distance
            FROM schema_metadata
            WHERE embedding IS NOT NULL
            ORDER BY embedding <=> %s::vector
            LIMIT %s
            """,
            (_vector_literal(vector), _vector_literal(vector), limit),
        )
    return cursor.fetchall()


def _query_sql_memory_vector_candidates(*, vector: list[float], limit: int) -> dict[str, float]:
    try:
        with get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute(
                """
                SELECT id::text, question_embedding <=> %s::vector AS distance
                FROM sql_memories
                WHERE question_embedding IS NOT NULL
                ORDER BY question_embedding <=> %s::vector
                LIMIT %s
                """,
                (_vector_literal(vector), _vector_literal(vector), limit),
            )
            rows = cursor.fetchall()
    except Exception:
        logger.warning("sql memory vector retrieval degraded", exc_info=True)
        return {}

    return {
        str(memory_id): _semantic_score(distance)
        for memory_id, distance in rows
    }


def _semantic_score(distance: Any) -> float:
    try:
        score = 1 - float(distance)
    except (TypeError, ValueError):
        return 0
    return round(max(0.0, min(score, 1.0)), 4)


def _vector_literal(vector: list[float]) -> str:
    return "[" + ",".join(f"{float(value):.8f}" for value in vector) + "]"
