from difflib import SequenceMatcher

from backend.app.db.repositories.memory_repository import SqlMemoryRepository
from backend.app.schemas.memories import (
    SqlMemoryCandidate,
    SqlMemoryRecord,
    SqlMemoryUpsert,
    SqlReusePlan,
)
from backend.app.tools.text_normalization import normalize_question


FAST_PATH_THRESHOLD = 0.88
REWRITE_PATH_THRESHOLD = 0.70


def retrieve_sql_memory(
    question: str,
    *,
    metrics: list[str],
    tables: list[str],
    limit: int = 5,
    repository: SqlMemoryRepository | None = None,
) -> list[SqlMemoryCandidate]:
    """确定性 SQL Memory 检索，后续可替换为 pgvector + pg_trgm 混合检索。"""
    repo = repository or SqlMemoryRepository()
    normalized_question = normalize_question(question)
    metric_set = set(metrics)
    table_set = set(tables)
    candidates: list[SqlMemoryCandidate] = []

    for memory in repo.list(limit=100):
        text_similarity = _text_similarity(normalized_question, memory.normalized_question)
        semantic_similarity = text_similarity
        metric_table_match = _metric_table_match(memory, metric_set, table_set)
        success_score = _success_score(memory)
        score = round(
            0.45 * semantic_similarity
            + 0.25 * text_similarity
            + 0.20 * metric_table_match
            + 0.10 * success_score,
            4,
        )
        if score <= 0:
            continue
        candidates.append(
            SqlMemoryCandidate(
                memory=memory,
                score=score,
                semantic_similarity=round(semantic_similarity, 4),
                text_similarity=round(text_similarity, 4),
                metric_table_match=round(metric_table_match, 4),
                success_score=round(success_score, 4),
            )
        )

    return sorted(candidates, key=lambda item: (-item.score, item.memory.created_at))[:limit]


def plan_sql_reuse(candidates: list[SqlMemoryCandidate]) -> SqlReusePlan:
    if not candidates:
        return SqlReusePlan(path_type="cold_path", candidate_count=0)

    selected = candidates[0]
    if selected.score >= FAST_PATH_THRESHOLD:
        return SqlReusePlan(
            path_type="fast_path",
            reuse_type="parameter_rewrite",
            memory_hit=True,
            selected_memory_id=selected.memory.id,
            selected_sql=selected.memory.final_sql,
            candidate_count=len(candidates),
            score=selected.score,
        )
    if selected.score >= REWRITE_PATH_THRESHOLD:
        return SqlReusePlan(
            path_type="rewrite_path",
            reuse_type="regenerate",
            memory_hit=False,
            selected_memory_id=selected.memory.id,
            candidate_count=len(candidates),
            score=selected.score,
        )
    return SqlReusePlan(
        path_type="cold_path",
        reuse_type="none",
        memory_hit=False,
        selected_memory_id=selected.memory.id,
        candidate_count=len(candidates),
        score=selected.score,
    )


def upsert_successful_sql_memory(
    *,
    question: str,
    sql_template: str,
    final_sql: str,
    tables: list[str],
    metrics: list[str],
    result_columns: list[str],
    row_count: int,
    latency_ms: int,
    parameters: dict | None = None,
    repository: SqlMemoryRepository | None = None,
) -> SqlMemoryRecord:
    repo = repository or SqlMemoryRepository()
    return repo.upsert_success(
        SqlMemoryUpsert(
            canonical_question=question,
            sql_template=sql_template,
            final_sql=final_sql,
            parameters=parameters or {},
            tables=tables,
            metrics=metrics,
            dimensions=["order_date"],
            result_columns=result_columns,
            row_count=row_count,
            latency_ms=latency_ms,
        )
    )


def _text_similarity(question: str, memory_question: str) -> float:
    if not question or not memory_question:
        return 0
    if question == memory_question:
        return 1
    return SequenceMatcher(None, question, memory_question).ratio()


def _metric_table_match(
    memory: SqlMemoryRecord,
    metric_set: set[str],
    table_set: set[str],
) -> float:
    memory_metrics = set(memory.metrics)
    memory_tables = set(memory.tables)
    metric_score = _overlap_score(memory_metrics, metric_set)
    table_score = _overlap_score(memory_tables, table_set)
    return (metric_score + table_score) / 2


def _overlap_score(left: set[str], right: set[str]) -> float:
    if not left or not right:
        return 0
    return len(left & right) / len(left | right)


def _success_score(memory: SqlMemoryRecord) -> float:
    total = memory.success_count + memory.failure_count
    if total <= 0:
        return 0
    return memory.success_count / total
