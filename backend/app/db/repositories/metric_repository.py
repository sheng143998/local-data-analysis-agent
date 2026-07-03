import json
from datetime import datetime, timezone
from uuid import UUID, uuid4

from backend.app.db.connection import get_connection
from backend.app.schemas.metrics import MetricCreate, MetricDefinition, MetricUpdate


class MetricRepository:
    """PostgreSQL 指标口径仓储。"""

    def list(self) -> list[MetricDefinition]:
        with get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute(
                """
                SELECT id, metric_name, display_name, description, formula,
                       required_tables, required_fields, default_filters,
                       example_question, owner, status, created_at, updated_at
                FROM metric_definitions
                ORDER BY display_name
                """
            )
            return [_row_to_metric(row) for row in cursor.fetchall()]

    def get(self, metric_id: UUID) -> MetricDefinition | None:
        with get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute(
                """
                SELECT id, metric_name, display_name, description, formula,
                       required_tables, required_fields, default_filters,
                       example_question, owner, status, created_at, updated_at
                FROM metric_definitions
                WHERE id = %s
                """,
                (str(metric_id),),
            )
            row = cursor.fetchone()
            return _row_to_metric(row) if row else None

    def create(self, payload: MetricCreate) -> MetricDefinition:
        metric_id = uuid4()
        now = datetime.now(timezone.utc)
        with get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute(
                """
                INSERT INTO metric_definitions (
                  id, metric_name, display_name, description, formula,
                  required_tables, required_fields, default_filters,
                  example_question, owner, status, created_at, updated_at
                )
                VALUES (%s, %s, %s, %s, %s, %s, %s, %s::jsonb, %s, %s, %s, %s, %s)
                """,
                (
                    str(metric_id),
                    payload.metric_name,
                    payload.display_name,
                    payload.description,
                    payload.formula,
                    payload.required_tables,
                    payload.required_fields,
                    json.dumps(payload.default_filters, ensure_ascii=False),
                    payload.example_question,
                    payload.owner,
                    payload.status,
                    now,
                    now,
                ),
            )
        created = self.get(metric_id)
        if created is None:
            raise RuntimeError("指标创建后无法读取")
        return created

    def update(self, metric_id: UUID, payload: MetricUpdate) -> MetricDefinition | None:
        current = self.get(metric_id)
        if current is None:
            return None

        data = current.model_dump()
        for key, value in payload.model_dump(exclude_unset=True).items():
            data[key] = value
        data["updated_at"] = datetime.now(timezone.utc)

        with get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute(
                """
                UPDATE metric_definitions
                SET metric_name = %s,
                    display_name = %s,
                    description = %s,
                    formula = %s,
                    required_tables = %s,
                    required_fields = %s,
                    default_filters = %s::jsonb,
                    example_question = %s,
                    owner = %s,
                    status = %s,
                    updated_at = %s
                WHERE id = %s
                """,
                (
                    data["metric_name"],
                    data["display_name"],
                    data["description"],
                    data["formula"],
                    data["required_tables"],
                    data["required_fields"],
                    json.dumps(data["default_filters"], ensure_ascii=False),
                    data["example_question"],
                    data["owner"],
                    data["status"],
                    data["updated_at"],
                    str(metric_id),
                ),
            )
        return self.get(metric_id)

    def delete(self, metric_id: UUID) -> bool:
        with get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute("DELETE FROM metric_definitions WHERE id = %s", (str(metric_id),))
            return cursor.rowcount > 0


def _row_to_metric(row) -> MetricDefinition:
    default_filters = row[7]
    if isinstance(default_filters, str):
        default_filters = json.loads(default_filters)

    return MetricDefinition(
        id=row[0],
        metric_name=row[1],
        display_name=row[2],
        description=row[3],
        formula=row[4],
        required_tables=list(row[5] or []),
        required_fields=list(row[6] or []),
        default_filters=default_filters or {},
        example_question=row[8],
        owner=row[9],
        status=row[10],
        created_at=row[11],
        updated_at=row[12],
    )
