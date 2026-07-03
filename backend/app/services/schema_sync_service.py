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
                    f"{column.table_name}.{column.column_name}",
                    f"业务表字段：{column.table_name}.{column.column_name}",
                ),
            )
        return len(columns)


def _normalize_filter(values: Iterable[str] | None) -> set[str]:
    if not values:
        return set()
    return {value.strip() for value in values if value and value.strip()}
