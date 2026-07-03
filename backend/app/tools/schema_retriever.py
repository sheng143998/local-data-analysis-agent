from backend.app.db.connection import get_connection
from backend.app.schemas.retrieval import MetricContext, SchemaColumnContext


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
    ranked = sorted(
        columns,
        key=lambda column: (
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
