from dataclasses import dataclass
from typing import Iterable

from backend.app.db.connection import get_connection


DEFAULT_EXCLUDED_TABLES = {
    "schema_metadata",
    "metric_definitions",
    "sql_memories",
    "query_runs",
    "tool_calls",
    "embedding_documents",
}


@dataclass(frozen=True)
class SchemaColumnSnapshot:
    table_name: str
    column_name: str
    data_type: str


@dataclass(frozen=True)
class SchemaSyncResult:
    scanned_columns: int
    synced_columns: int
    tables: list[str]


class SchemaSyncService:
    """同步真实 PostgreSQL 表结构到 schema_metadata。"""

    def sync_public_schema(
        self,
        include_tables: Iterable[str] | None = None,
        exclude_tables: Iterable[str] | None = None,
    ) -> SchemaSyncResult:
        includes = _normalize_filter(include_tables)
        excludes = DEFAULT_EXCLUDED_TABLES | _normalize_filter(exclude_tables)

        with get_connection() as conn:
            cursor = conn.cursor()
            columns = self._load_public_columns(cursor, includes, excludes)
            synced = self._upsert_schema_metadata(cursor, columns)

        return SchemaSyncResult(
            scanned_columns=len(columns),
            synced_columns=synced,
            tables=sorted({column.table_name for column in columns}),
        )

    def _load_public_columns(
        self,
        cursor,
        include_tables: set[str],
        exclude_tables: set[str],
    ) -> list[SchemaColumnSnapshot]:
        cursor.execute(
            """
            SELECT table_name, column_name, data_type
            FROM information_schema.columns
            WHERE table_schema = 'public'
              AND table_name <> ALL(%s::text[])
              AND (%s::text[] = '{}'::text[] OR table_name = ANY(%s::text[]))
            ORDER BY table_name, ordinal_position
            """,
            (list(exclude_tables), list(include_tables), list(include_tables)),
        )
        return [
            SchemaColumnSnapshot(table_name=row[0], column_name=row[1], data_type=row[2])
            for row in cursor.fetchall()
        ]

    def _upsert_schema_metadata(self, cursor, columns: list[SchemaColumnSnapshot]) -> int:
        for column in columns:
            description = infer_schema_description(column)
            business_meaning = infer_schema_business_meaning(column)
            cursor.execute(
                """
                INSERT INTO schema_metadata (
                  table_name, column_name, data_type, description, business_meaning, updated_at
                )
                VALUES (%s, %s, %s, %s, %s, now())
                ON CONFLICT (table_name, column_name) DO UPDATE SET
                  data_type = EXCLUDED.data_type,
                  description = CASE
                    WHEN schema_metadata.description = ''
                    THEN EXCLUDED.description
                    ELSE schema_metadata.description
                  END,
                  business_meaning = CASE
                    WHEN schema_metadata.business_meaning = ''
                    THEN EXCLUDED.business_meaning
                    ELSE schema_metadata.business_meaning
                  END,
                  updated_at = now()
                """,
                (
                    column.table_name,
                    column.column_name,
                    column.data_type,
                    description,
                    business_meaning,
                ),
            )
        return len(columns)


def _normalize_filter(values: Iterable[str] | None) -> set[str]:
    if not values:
        return set()
    return {value.strip() for value in values if value and value.strip()}


def infer_schema_description(column: SchemaColumnSnapshot) -> str:
    label = _column_label(column.column_name)
    return f"{column.table_name}.{column.column_name}，{label}，类型为 {column.data_type}"


def infer_schema_business_meaning(column: SchemaColumnSnapshot) -> str:
    column_name = column.column_name.lower()
    table_label = _table_label(column.table_name)
    type_hint = _data_type_hint(column.data_type)

    if column_name == "id":
        return f"{table_label}的主键标识，用于唯一识别记录和关联其他表。"
    if column_name.endswith("_id"):
        target = column_name.removesuffix("_id")
        return f"关联{_entity_label(target)}的标识字段，常用于跨表 join 和分组分析。"
    if column_name in {"created_at", "create_time", "created_time"}:
        return f"{table_label}的创建时间，可用于时间趋势、近 N 天筛选和分组。"
    if column_name in {"updated_at", "update_time", "updated_time"}:
        return f"{table_label}的更新时间，可用于识别最近变更的数据。"
    if column_name.endswith("_at") or "date" in column_name or "time" in column_name:
        return f"{table_label}的时间字段，可用于时间范围筛选和时间维度分析。"
    if column_name in {"status", "state"} or column_name.endswith("_status"):
        return f"{table_label}的状态字段，可用于过滤有效记录、分组统计和状态对比。"
    if _contains_any(column_name, ["amount", "price", "cost", "value", "revenue", "sales", "fee"]):
        return f"{table_label}的金额类指标字段，可用于求和、均值、占比和规模分析。"
    if _contains_any(column_name, ["count", "qty", "quantity", "num", "stock"]):
        return f"{table_label}的数量类字段，可用于库存、次数、规模或计数分析。"
    if _contains_any(column_name, ["rate", "ratio", "percent", "margin"]):
        return f"{table_label}的比例类字段，可用于转化率、占比、毛利率等分析。"
    if column_name in {"city", "province", "state", "region", "country"}:
        return f"{table_label}的地域维度字段，可用于城市、地区或国家分组分析。"
    if _contains_any(column_name, ["category", "type", "kind", "source", "channel"]):
        return f"{table_label}的分类维度字段，可用于分类、来源、渠道或类型对比。"
    if _contains_any(column_name, ["name", "title", "code"]):
        return f"{table_label}的名称或编码字段，可用于展示、搜索和维度分组。"
    if _contains_any(column_name, ["score", "rating", "rank"]):
        return f"{table_label}的评分或排序字段，可用于质量、满意度或优先级分析。"
    if _contains_any(column_name, ["reason", "comment", "message", "description"]):
        return f"{table_label}的文本说明字段，可用于原因分析、备注检索和内容理解。"

    return f"{table_label}的业务字段，{type_hint}，可结合问题语义用于筛选、分组或展示。"


def _column_label(column_name: str) -> str:
    normalized = column_name.lower()
    if normalized == "id":
        return "主键标识字段"
    if normalized.endswith("_id"):
        return "关联标识字段"
    if normalized.endswith("_at") or "date" in normalized or "time" in normalized:
        return "时间字段"
    if normalized in {"status", "state"} or normalized.endswith("_status"):
        return "状态字段"
    if _contains_any(normalized, ["amount", "price", "cost", "value", "revenue", "sales", "fee"]):
        return "金额字段"
    if _contains_any(normalized, ["count", "qty", "quantity", "num", "stock"]):
        return "数量字段"
    if _contains_any(normalized, ["rate", "ratio", "percent", "margin"]):
        return "比例字段"
    return "业务字段"


def _table_label(table_name: str) -> str:
    return table_name.replace("_", " ")


def _entity_label(name: str) -> str:
    return name.replace("_", " ")


def _data_type_hint(data_type: str) -> str:
    normalized = data_type.lower()
    if any(token in normalized for token in ["int", "numeric", "decimal", "double", "real"]):
        return "通常可作为数值计算或排序字段"
    if any(token in normalized for token in ["timestamp", "date", "time"]):
        return "通常可作为时间筛选或趋势分析字段"
    if "bool" in normalized:
        return "通常可作为真假条件或状态过滤字段"
    return "通常可作为筛选、展示或分组字段"


def _contains_any(text: str, tokens: list[str]) -> bool:
    return any(token in text for token in tokens)
