from backend.app.schemas.retrieval import MetricContext, RetrievalContext, SchemaColumnContext
from backend.app.tools.metric_retriever import retrieve_metrics
from backend.app.tools.schema_retriever import retrieve_schema


def build_retrieval_context(question: str) -> RetrievalContext:
    """组合指标口径和表结构上下文，供 Agent 后续节点使用。"""
    metrics = retrieve_metrics(question)
    schema_columns = retrieve_schema(question, metrics)
    return RetrievalContext(
        metrics=metrics,
        schema_columns=schema_columns,
        tables=_unique_tables(metrics, schema_columns),
        fields=_unique_fields(metrics, schema_columns),
        metric_summary=_metric_summary(metrics),
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


def _metric_summary(metrics: list[MetricContext]) -> str:
    if not metrics:
        return "未召回明确指标口径"
    return "；".join(
        f"{metric.display_name} = {metric.description}"
        for metric in metrics
    )
