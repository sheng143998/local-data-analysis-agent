from backend.app.schemas.retrieval import (
    MetricContext,
    RetrievalContext,
    SchemaColumnContext,
    TableRelationshipContext,
)
from backend.app.tools.metric_retriever import retrieve_metrics
from backend.app.tools.schema_retriever import retrieve_schema


def build_retrieval_context(question: str) -> RetrievalContext:
    """组合指标口径和表结构上下文，供 Agent 后续节点使用。"""
    metrics = retrieve_metrics(question)
    schema_columns = retrieve_schema(question, metrics)
    return RetrievalContext(
        metrics=metrics,
        schema_columns=schema_columns,
        table_relationships=infer_table_relationships(schema_columns),
        tables=_unique_tables(metrics, schema_columns),
        fields=_unique_fields(metrics, schema_columns),
        metric_summary=_metric_summary(metrics),
    )


def infer_table_relationships(
    schema_columns: list[SchemaColumnContext],
    limit: int = 24,
) -> list[TableRelationshipContext]:
    """根据已召回字段推断高置信表连接关系，供 SQL Generator 使用。"""
    fields_by_table: dict[str, set[str]] = {}
    for column in schema_columns:
        fields_by_table.setdefault(column.table_name, set()).add(column.column_name)

    relationships: list[TableRelationshipContext] = []
    seen: set[tuple[str, str, str, str]] = set()

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


def _metric_summary(metrics: list[MetricContext]) -> str:
    if not metrics:
        return "未召回明确指标口径"
    return "；".join(
        f"{metric.display_name} = {metric.description}"
        for metric in metrics
    )


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
