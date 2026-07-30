import logging
import re
import threading

from backend.app.core.config import settings
from backend.app.schemas.retrieval import (
    MetricContext,
    RetrievalContext,
    SchemaColumnContext,
    TableRelationshipContext,
)
from backend.app.db.connection import get_connection
from backend.app.tools.context_reranker import rerank_context
from backend.app.tools.metric_retriever import retrieve_metrics
from backend.app.tools.schema_retriever import retrieve_schema


logger = logging.getLogger("backend.retrieval")

DEFAULT_RELATIONSHIP_LIMIT = 24

# 低基数枚举列命名特征：这些列的真实取值样本会被注入生成提示词（计划 3b-lite），
# 直接消除 "status='completed'（库里其实叫 delivered）" 这类取值幻觉。
_SAMPLE_VALUE_COLUMN_TOKENS = ("status", "type", "category", "method", "source", "channel", "state", "reason")
_SAMPLE_VALUE_DATA_TYPES = ("text", "character", "varchar", "char")

_sample_values_cache: dict[tuple[str, str], list[str]] = {}
_sample_values_lock = threading.Lock()


def clear_sample_values_cache() -> None:
    with _sample_values_lock:
        _sample_values_cache.clear()


def attach_sample_values(schema_columns: list[SchemaColumnContext]) -> list[SchemaColumnContext]:
    """为召回的低基数枚举列补充数据库真实取值样本。

    只处理命名与类型都符合枚举特征的列；取值查询走白名单标识符 +
    进程内缓存（枚举取值极少变化），失败静默降级为无样本。
    """
    limit = settings.sample_values_per_column
    if limit <= 0:
        return schema_columns
    enriched: list[SchemaColumnContext] = []
    for column in schema_columns:
        if _is_sample_value_candidate(column):
            values = _load_sample_values(column.table_name, column.column_name, limit)
            if values:
                column = column.model_copy(update={"sample_values": values})
        enriched.append(column)
    return enriched


def _is_sample_value_candidate(column: SchemaColumnContext) -> bool:
    name = column.column_name.lower()
    data_type = (column.data_type or "").lower()
    return any(token in name for token in _SAMPLE_VALUE_COLUMN_TOKENS) and any(
        token in data_type for token in _SAMPLE_VALUE_DATA_TYPES
    )


def _load_sample_values(table_name: str, column_name: str, limit: int) -> list[str]:
    # 标识符不可参数化：仅允许安全字符，防注入。
    if not re.fullmatch(r"[A-Za-z_][A-Za-z0-9_]*", table_name) or not re.fullmatch(
        r"[A-Za-z_][A-Za-z0-9_]*", column_name
    ):
        return []
    cache_key = (table_name, column_name)
    with _sample_values_lock:
        if cache_key in _sample_values_cache:
            return list(_sample_values_cache[cache_key])
    try:
        with get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute(
                f'SELECT DISTINCT "{column_name}" FROM "{table_name}" '
                f'WHERE "{column_name}" IS NOT NULL LIMIT %s',
                (limit + 1,),
            )
            rows = [str(row[0]) for row in cursor.fetchall()]
    except Exception:  # noqa: BLE001 - 样本值缺失不阻断检索
        logger.warning("sample values lookup degraded for %s.%s", table_name, column_name, exc_info=True)
        return []
    # 超过上限说明不是低基数枚举列，不注入以免误导模型。
    values = sorted(rows)[:limit] if len(rows) <= limit else []
    with _sample_values_lock:
        _sample_values_cache[cache_key] = list(values)
    return values


def build_retrieval_context(
    question: str,
    semantic_contracts: list[dict] | None = None,
    query_plan: dict | None = None,
    *,
    question_vector: list[float] | None = None,
    precomputed_metrics: list[MetricContext] | None = None,
    precomputed_schema: list[SchemaColumnContext] | None = None,
) -> RetrievalContext:
    """组合指标口径和表结构上下文，供 Agent 后续节点使用。

    precomputed_*：意图解析阶段并行预取的检索产物（计划 2b）；提供时跳过
    重复检索，只做 rerank、契约合并与关系推断。
    """
    metrics = (
        precomputed_metrics
        if precomputed_metrics is not None
        else retrieve_metrics(question, question_vector=question_vector)
    )
    schema_columns = (
        precomputed_schema
        if precomputed_schema is not None
        else retrieve_schema(question, metrics, question_vector=question_vector)
    )
    schema_columns = attach_sample_values(schema_columns)
    metrics, schema_columns, rerank_diagnostics = rerank_context(question, metrics, schema_columns)
    contracts = semantic_contracts or []
    plan = query_plan or {}
    contract_tables = [table for contract in contracts for table in contract.get("source_tables", [])]
    contract_tables.extend(plan.get("entities", []))
    contract_fields = [field for contract in contracts for field in contract.get("source_fields", [])]
    contract_summary = "；".join(
        f"{contract.get('display_name', contract.get('contract_key', ''))}@v{contract.get('version', '')}"
        for contract in contracts
    )
    return RetrievalContext(
        metrics=metrics,
        schema_columns=schema_columns,
        table_relationships=infer_table_relationships(
            schema_columns,
            include_database_foreign_keys=True,
        ),
        tables=_merge_unique(_unique_tables(metrics, schema_columns), contract_tables),
        fields=_merge_unique(_unique_fields(metrics, schema_columns), contract_fields),
        metric_summary="；".join(item for item in [_metric_summary(metrics), contract_summary] if item),
        rerank_diagnostics=rerank_diagnostics.as_dict(),
    )


def infer_table_relationships(
    schema_columns: list[SchemaColumnContext],
    limit: int = DEFAULT_RELATIONSHIP_LIMIT,
    include_database_foreign_keys: bool = False,
) -> list[TableRelationshipContext]:
    """根据已召回字段推断高置信表连接关系，供 SQL Generator 使用。"""
    fields_by_table: dict[str, set[str]] = {}
    for column in schema_columns:
        fields_by_table.setdefault(column.table_name, set()).add(column.column_name)

    relationships: list[TableRelationshipContext] = []
    seen: set[tuple[str, str, str, str]] = set()

    if include_database_foreign_keys:
        try:
            database_relationships = _load_postgres_foreign_key_relationships(fields_by_table)
        except Exception:
            logger.warning("foreign key introspection degraded", exc_info=True)
            database_relationships = []
        for relationship in database_relationships:
            _append_relationship(
                relationships,
                seen,
                relationship.left_table,
                relationship.left_column,
                relationship.right_table,
                relationship.right_column,
                relationship.relationship_type,
                relationship.confidence,
                relationship.reason,
            )

    for left_table in sorted(fields_by_table):
        for right_table in sorted(fields_by_table):
            if left_table >= right_table:
                continue
            shared_keys = sorted(
                column
                for column in fields_by_table[left_table] & fields_by_table[right_table]
                if _is_join_key(column)
            )
            for column in shared_keys:
                _append_relationship(
                    relationships,
                    seen,
                    left_table,
                    column,
                    right_table,
                    column,
                    "same_key",
                    0.86,
                    f"两个表都包含可连接字段 {column}",
                )

    for parent_table, columns in fields_by_table.items():
        if "id" not in columns:
            continue
        parent_key = f"{_singularize(parent_table)}_id"
        for child_table, child_columns in fields_by_table.items():
            if child_table == parent_table or parent_key not in child_columns:
                continue
            _append_relationship(
                relationships,
                seen,
                parent_table,
                "id",
                child_table,
                parent_key,
                "id_to_foreign_key",
                0.92,
                f"{child_table}.{parent_key} 命名上指向 {parent_table}.id",
            )

    return sorted(
        relationships,
        key=lambda item: (
            -item.confidence,
            item.left_table,
            item.right_table,
            item.left_column,
            item.right_column,
        ),
    )[:limit]


def _load_postgres_foreign_key_relationships(
    fields_by_table: dict[str, set[str]],
) -> list[TableRelationshipContext]:
    if not fields_by_table:
        return []
    try:
        with get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute(
                """
                SELECT
                  ccu.table_name AS parent_table,
                  ccu.column_name AS parent_column,
                  kcu.table_name AS child_table,
                  kcu.column_name AS child_column,
                  tc.constraint_name
                FROM information_schema.table_constraints tc
                JOIN information_schema.key_column_usage kcu
                  ON tc.constraint_name = kcu.constraint_name
                 AND tc.table_schema = kcu.table_schema
                 AND tc.constraint_catalog = kcu.constraint_catalog
                JOIN information_schema.constraint_column_usage ccu
                  ON ccu.constraint_name = tc.constraint_name
                 AND ccu.table_schema = tc.table_schema
                 AND ccu.constraint_catalog = tc.constraint_catalog
                WHERE tc.constraint_type = 'FOREIGN KEY'
                  AND tc.table_schema = 'public'
                ORDER BY ccu.table_name, kcu.table_name, kcu.column_name
                """
            )
            rows = cursor.fetchall()
    except Exception:
        logger.warning("foreign key query degraded", exc_info=True)
        return []

    relationships: list[TableRelationshipContext] = []
    for parent_table, parent_column, child_table, child_column, constraint_name in rows:
        if not _relationship_columns_are_recalled(
            fields_by_table,
            str(parent_table),
            str(parent_column),
            str(child_table),
            str(child_column),
        ):
            continue
        relationships.append(
            TableRelationshipContext(
                left_table=str(parent_table),
                left_column=str(parent_column),
                right_table=str(child_table),
                right_column=str(child_column),
                relationship_type="foreign_key",
                confidence=0.98,
                reason=f"PostgreSQL 外键约束 {constraint_name}",
            )
        )
    return relationships


def _relationship_columns_are_recalled(
    fields_by_table: dict[str, set[str]],
    parent_table: str,
    parent_column: str,
    child_table: str,
    child_column: str,
) -> bool:
    return (
        parent_column in fields_by_table.get(parent_table, set())
        and child_column in fields_by_table.get(child_table, set())
    )


def _unique_tables(
    metrics: list[MetricContext],
    schema_columns: list[SchemaColumnContext],
) -> list[str]:
    tables: list[str] = []
    for metric in metrics:
        for table in metric.required_tables:
            if table not in tables:
                tables.append(table)
    for column in schema_columns:
        if column.table_name not in tables:
            tables.append(column.table_name)
    return tables


def _unique_fields(
    metrics: list[MetricContext],
    schema_columns: list[SchemaColumnContext],
) -> list[str]:
    fields: list[str] = []
    for metric in metrics:
        for field in metric.required_fields:
            if field not in fields:
                fields.append(field)
    for column in schema_columns:
        field = f"{column.table_name}.{column.column_name}"
        if field not in fields:
            fields.append(field)
    return fields


def _merge_unique(existing: list[str], additions: list[str]) -> list[str]:
    return list(dict.fromkeys([*existing, *[str(item) for item in additions if item]]))


def _append_relationship(
    relationships: list[TableRelationshipContext],
    seen: set[tuple[str, str, str, str]],
    left_table: str,
    left_column: str,
    right_table: str,
    right_column: str,
    relationship_type: str,
    confidence: float,
    reason: str,
) -> None:
    key = _relationship_key(left_table, left_column, right_table, right_column)
    if key in seen:
        return
    seen.add(key)
    relationships.append(
        TableRelationshipContext(
            left_table=left_table,
            left_column=left_column,
            right_table=right_table,
            right_column=right_column,
            relationship_type=relationship_type,
            confidence=confidence,
            reason=reason,
        )
    )


def _relationship_key(
    left_table: str,
    left_column: str,
    right_table: str,
    right_column: str,
) -> tuple[str, str, str, str]:
    left = (left_table, left_column)
    right = (right_table, right_column)
    first, second = sorted([left, right])
    return first[0], first[1], second[0], second[1]


def _is_join_key(column_name: str) -> bool:
    return column_name == "id" or column_name.endswith("_id")


def _singularize(table_name: str) -> str:
    if table_name.endswith("ies"):
        return f"{table_name[:-3]}y"
    if table_name.endswith("s"):
        return table_name[:-1]
    return table_name


def _metric_summary(
    metrics: list[MetricContext],
) -> str:
    if not metrics:
        return "未召回明确指标口径"
    return "；".join(
        f"{metric.display_name} = {metric.description}"
        for metric in metrics
    )
