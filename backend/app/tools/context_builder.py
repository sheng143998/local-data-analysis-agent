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


DEFAULT_RELATIONSHIP_LIMIT = 24


def build_retrieval_context(question: str, semantic_contracts: list[dict] | None = None) -> RetrievalContext:
    """组合指标口径和表结构上下文，供 Agent 后续节点使用。"""
    metrics = retrieve_metrics(question)
    schema_columns = retrieve_schema(question, metrics)
    metrics, schema_columns, rerank_diagnostics = rerank_context(question, metrics, schema_columns)
    contracts = semantic_contracts or []
    contract_tables = [table for contract in contracts for table in contract.get("source_tables", [])]
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
