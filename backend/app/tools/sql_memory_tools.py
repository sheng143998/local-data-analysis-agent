from backend.app.db.repositories.memory_repository import SqlMemoryRepository
from backend.app.schemas.memories import (
    SqlMemoryCandidate,
    SqlMemoryRecord,
    SqlMemoryUpsert,
    SqlReusePlan,
)
from backend.app.tools.retrieval_scoring import overlap_score, text_similarity
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
    required_tables = _required_tables_for_question(question)
    candidates: list[SqlMemoryCandidate] = []

    for memory in repo.list(limit=100):
        lexical_similarity = text_similarity(normalized_question, memory.normalized_question)
        semantic_similarity = lexical_similarity
        metric_table_match = _metric_table_match(memory, metric_set, table_set)
        success_score = _success_score(memory)
        score = round(
            0.45 * semantic_similarity
            + 0.25 * lexical_similarity
            + 0.20 * metric_table_match
            + 0.10 * success_score,
            4,
        )
        if score <= 0:
            continue
        required_table_match = _sql_contains_required_tables(memory.final_sql, required_tables)
        candidates.append(
            SqlMemoryCandidate(
                memory=memory,
                score=score,
                semantic_similarity=round(semantic_similarity, 4),
                text_similarity=round(lexical_similarity, 4),
                metric_table_match=round(metric_table_match, 4),
                success_score=round(success_score, 4),
                required_table_match=required_table_match,
                required_tables=required_tables,
            )
        )

    return sorted(candidates, key=lambda item: (-item.score, item.memory.created_at))[:limit]


def plan_sql_reuse(candidates: list[SqlMemoryCandidate]) -> SqlReusePlan:
    if not candidates:
        return SqlReusePlan(path_type="cold_path", candidate_count=0)

    selected = candidates[0]
    if selected.score >= FAST_PATH_THRESHOLD and selected.required_table_match:
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


def _metric_table_match(
    memory: SqlMemoryRecord,
    metric_set: set[str],
    table_set: set[str],
) -> float:
    memory_metrics = set(memory.metrics)
    memory_tables = set(memory.tables)
    metric_score = overlap_score(memory_metrics, metric_set)
    table_score = overlap_score(memory_tables, table_set)
    return (metric_score + table_score) / 2


def _success_score(memory: SqlMemoryRecord) -> float:
    total = memory.success_count + memory.failure_count
    if total <= 0:
        return 0
    return memory.success_count / total


def _required_tables_for_question(question: str) -> list[str]:
    required: list[str] = []
    if any(token in question for token in ["新增用户", "新用户", "下单用户", "购买用户", "购买次数最多", "用户是谁"]):
        required.append("users")
    if any(token in question for token in ["访问", "加购", "流量来源", "转化率"]):
        required.append("traffic_events")
    if any(token in question for token in ["优惠券", "核销"]):
        required.append("coupon_usages")
    if any(token in question for token in ["哪些优惠券", "优惠券核销"]):
        required.append("coupons")
    return required


def _sql_contains_required_tables(sql: str, required_tables: list[str]) -> bool:
    if not required_tables:
        return True
    lowered_sql = sql.lower()
    return all(table.lower() in lowered_sql for table in required_tables)
