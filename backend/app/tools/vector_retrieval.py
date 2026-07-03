from __future__ import annotations

from dataclasses import dataclass
from typing import Any, Literal

from backend.app.core.embedding_adapter import EmbeddingAdapter, EmbeddingRequest
from backend.app.db.connection import get_connection


VectorTarget = Literal["metric", "schema"]


@dataclass(frozen=True)
class VectorCandidate:
    key: str
    score: float


def retrieve_metric_vector_candidates(
    question: str,
    *,
    limit: int = 8,
    adapter: EmbeddingAdapter | None = None,
) -> dict[str, float]:
    vector = _embed_question(question, adapter=adapter)
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
) -> dict[str, float]:
    vector = _embed_question(question, adapter=adapter)
    if not vector:
        return {}
    return _query_vector_candidates(
        target="schema",
        vector=vector,
        limit=limit,
        tables=tables,
    )


def _embed_question(question: str, *, adapter: EmbeddingAdapter | None = None) -> list[float]:
    if not question.strip():
        return []
    response = (adapter or EmbeddingAdapter()).embed(EmbeddingRequest(texts=[question]))
    if not response.ok or not response.vectors:
        return []
    return response.vectors[0]


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


def _semantic_score(distance: Any) -> float:
    try:
        score = 1 - float(distance)
    except (TypeError, ValueError):
        return 0
    return round(max(0.0, min(score, 1.0)), 4)


def _vector_literal(vector: list[float]) -> str:
    return "[" + ",".join(f"{float(value):.8f}" for value in vector) + "]"
