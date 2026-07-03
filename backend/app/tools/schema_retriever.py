from backend.app.db.connection import get_connection
from backend.app.schemas.retrieval import MetricContext, SchemaColumnContext
from backend.app.tools.retrieval_scoring import (
    build_search_document,
    keyword_hit_score,
    text_similarity,
    weighted_score,
)


DEFAULT_ANALYSIS_TABLES = ["orders", "payments", "refunds"]


def retrieve_schema(
    question: str,
    metrics: list[MetricContext],
    limit_per_table: int = 12,
) -> list[SchemaColumnContext]:
    """根据问题和指标所需表字段召回 schema_metadata。"""
    tables = _related_tables(question, metrics)
    required_fields = {
        field
        for metric in metrics
        for field in metric.required_fields
        if "." in field
    }
    columns = _load_schema_columns(tables)
    scored_columns = [
        _score_column(column, question, related_tables=tables, required_fields=required_fields)
        for column in columns
    ]
    ranked = sorted(
        scored_columns,
        key=lambda column: (
            -column.score,
            column.table_name not in tables,
            f"{column.table_name}.{column.column_name}" not in required_fields,
            _column_priority(column.column_name),
            column.table_name,
            column.column_name,
        ),
    )

    table_counts: dict[str, int] = {}
    selected: list[SchemaColumnContext] = []
    for column in ranked:
        count = table_counts.get(column.table_name, 0)
        if count >= limit_per_table:
            continue
        selected.append(column)
        table_counts[column.table_name] = count + 1
    return selected


def _related_tables(question: str, metrics: list[MetricContext]) -> list[str]:
    tables: list[str] = []
    for metric in metrics:
        for table in metric.required_tables:
            if table not in tables:
                tables.append(table)

    if any(token in question for token in ["退款", "退款率", "售后"]) and "refunds" not in tables:
        tables.append("refunds")
        for table in ["order_items", "products", "payments"]:
            if table not in tables:
                tables.append(table)
    if any(token in question for token in ["毛利率", "毛利", "利润率"]):
        for table in ["order_items", "products", "product_costs", "payments"]:
            if table not in tables:
                tables.append(table)
    if any(token in question for token in ["复购率", "复购", "回购", "城市", "地区", "地域", "客单价"]):
        for table in ["users", "orders", "payments", "refunds"]:
            if table not in tables:
                tables.append(table)
    if any(token in question for token in ["支付", "已支付", "销售额"]) and "payments" not in tables:
        tables.append("payments")
    if any(token in question for token in ["商品", "产品", "SKU", "sku", "品类", "类目", "分类"]):
        for table in ["order_items", "products", "payments"]:
            if table not in tables:
                tables.append(table)
    if "orders" not in tables:
        tables.insert(0, "orders")

    return tables or DEFAULT_ANALYSIS_TABLES


def _load_schema_columns(tables: list[str]) -> list[SchemaColumnContext]:
    with get_connection() as conn:
        cursor = conn.cursor()
        cursor.execute(
            """
            SELECT table_name, column_name, data_type, description, business_meaning
            FROM schema_metadata
            WHERE table_name = ANY(%s)
            ORDER BY table_name, column_name
            """,
            (tables,),
        )
        return [
            SchemaColumnContext(
                table_name=row[0],
                column_name=row[1],
                data_type=row[2],
                description=row[3],
                business_meaning=row[4],
            )
            for row in cursor.fetchall()
        ]


def _column_priority(column_name: str) -> int:
    priorities = {
        "created_at": 0,
        "total_amount": 1,
        "status": 2,
        "order_id": 3,
        "id": 4,
    }
    return priorities.get(column_name, 10)


def _score_column(
    column: SchemaColumnContext,
    question: str,
    *,
    related_tables: list[str],
    required_fields: set[str],
) -> SchemaColumnContext:
    field_name = f"{column.table_name}.{column.column_name}"
    document = build_search_document(
        [
            column.table_name,
            column.column_name,
            column.data_type,
            column.description,
            column.business_meaning,
        ]
    )
    required_field_match = 1.0 if field_name in required_fields else 0.0
    related_table_match = 1.0 if column.table_name in related_tables else 0.0
    keyword_score = keyword_hit_score(
        question,
        {
            column.table_name,
            column.column_name,
            field_name,
            column.description,
            column.business_meaning,
        },
    )
    similarity = text_similarity(question, document)
    priority_score = max(0.0, (10 - _column_priority(column.column_name)) / 10)
    score = weighted_score(
        {
            "required_field_match": (required_field_match, 1.0),
            "related_table_match": (related_table_match, 0.2),
            "keyword_score": (keyword_score, 0.8),
            "text_similarity": (similarity, 0.4),
            "priority_score": (priority_score, 0.2),
        }
    )
    return column.model_copy(update={"score": score})
