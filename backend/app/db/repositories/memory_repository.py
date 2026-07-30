import json
from uuid import UUID, uuid4

from backend.app.core.config import settings
from backend.app.db.connection import get_connection
from backend.app.schemas.memories import SqlMemoryRecord, SqlMemoryUpsert
from backend.app.tools.text_normalization import normalize_question


# 自动可信状态机不会触碰的终态：人工弃用/拒绝后不允许自动复活。
_AUTO_PROMOTE_BLOCKED = {"deprecated", "rejected"}


class SqlMemoryRepository:
    """PostgreSQL SQL Memory 仓储。"""

    def list(self, limit: int = 50) -> list[SqlMemoryRecord]:
        with get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute(
                """
                SELECT id, canonical_question, normalized_question, question_pattern,
                       intent, sql_template, final_sql, param_schema, parameters,
                       tables, metrics, dimensions, filters, dialect, schema_version,
                       success_count, failure_count, avg_latency_ms, last_result_columns,
                       last_row_count, last_used_at, created_at
                FROM sql_memories
                ORDER BY last_used_at DESC NULLS LAST, created_at DESC
                LIMIT %s
                """,
                (limit,),
            )
            return [_row_to_memory(row) for row in cursor.fetchall()]

    def get(self, memory_id: UUID) -> SqlMemoryRecord | None:
        with get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute(
                """
                SELECT id, canonical_question, normalized_question, question_pattern,
                       intent, sql_template, final_sql, param_schema, parameters,
                       tables, metrics, dimensions, filters, dialect, schema_version,
                       success_count, failure_count, avg_latency_ms, last_result_columns,
                       last_row_count, last_used_at, created_at
                FROM sql_memories
                WHERE id = %s
                """,
                (str(memory_id),),
            )
            row = cursor.fetchone()
            return _row_to_memory(row) if row else None

    def upsert_success(self, payload: SqlMemoryUpsert) -> SqlMemoryRecord:
        normalized_question = normalize_question(payload.canonical_question)
        existing = self._get_by_normalized_question(normalized_question)
        if existing is None:
            created = self._create_success(payload, normalized_question)
            if created is not None:
                return created
            # 并发下另一请求先插入（unique index 兜底）：改走更新路径。
            existing = self._get_by_normalized_question(normalized_question)
            if existing is None:  # pragma: no cover - 极端竞态防御
                raise RuntimeError("sql memory upsert race could not be resolved")
        return self._update_success(existing, payload)

    def get_by_normalized_question(self, normalized_question: str) -> SqlMemoryRecord | None:
        """按归一化问题精确取记忆（记忆优先快路径用）。"""
        return self._get_by_normalized_question(normalized_question)

    def record_failure(self, memory_id: UUID, *, reason: str = "") -> SqlMemoryRecord | None:
        """记录一次复用执行失败：失败计数 +1、连续成功清零；verified 记忆降级。

        计划 1a：任何一次执行失败都会打断自动可信状态机；已 verified 的记忆
        降级为 reviewed（保留 SQL 与历史供审计），降级原因写入 filters。
        """
        memory = self.get(memory_id)
        if memory is None:
            return None
        filters = dict(memory.filters)
        filters["auto_verify_streak"] = 0
        current_status = filters.get("trust_status", memory.trust_status)
        if current_status == "verified":
            filters["trust_status"] = "reviewed"
            filters["demoted_reason"] = reason or "execution_failure"
        with get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute(
                """
                UPDATE sql_memories
                SET failure_count = failure_count + 1,
                    filters = %s::jsonb,
                    last_used_at = now()
                WHERE id = %s
                RETURNING id, canonical_question, normalized_question, question_pattern,
                          intent, sql_template, final_sql, param_schema, parameters,
                          tables, metrics, dimensions, filters, dialect, schema_version,
                          success_count, failure_count, avg_latency_ms, last_result_columns,
                          last_row_count, last_used_at, created_at
                """,
                (json.dumps(filters, ensure_ascii=False), str(memory_id)),
            )
            row = cursor.fetchone()
            return _row_to_memory(row) if row else None

    def update_trust_status(self, memory_id: UUID, trust_status: str) -> SqlMemoryRecord | None:
        """仅更新审核状态，保留 SQL、成功次数和历史参数以便审计。"""
        with get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute(
                """
                UPDATE sql_memories
                SET filters = jsonb_set(COALESCE(filters, '{}'::jsonb), '{trust_status}', to_jsonb(%s::text), true)
                WHERE id = %s
                RETURNING id, canonical_question, normalized_question, question_pattern,
                          intent, sql_template, final_sql, param_schema, parameters,
                          tables, metrics, dimensions, filters, dialect, schema_version,
                          success_count, failure_count, avg_latency_ms, last_result_columns,
                          last_row_count, last_used_at, created_at
                """,
                (trust_status, str(memory_id)),
            )
            row = cursor.fetchone()
            return _row_to_memory(row) if row else None

    def _get_by_normalized_question(self, normalized_question: str) -> SqlMemoryRecord | None:
        with get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute(
                """
                SELECT id, canonical_question, normalized_question, question_pattern,
                       intent, sql_template, final_sql, param_schema, parameters,
                       tables, metrics, dimensions, filters, dialect, schema_version,
                       success_count, failure_count, avg_latency_ms, last_result_columns,
                       last_row_count, last_used_at, created_at
                FROM sql_memories
                WHERE normalized_question = %s
                ORDER BY created_at DESC
                LIMIT 1
                """,
                (normalized_question,),
            )
            row = cursor.fetchone()
            return _row_to_memory(row) if row else None

    def _create_success(
        self,
        payload: SqlMemoryUpsert,
        normalized_question: str,
    ) -> SqlMemoryRecord | None:
        memory_id = uuid4()
        filters = _memory_filters(payload)
        filters["auto_verify_streak"] = 1
        # 阈值为 1 时首个成功即满足"连续 N 次"——与更新路径的状态机保持一致。
        if (
            settings.memory_auto_verify_threshold <= 1
            and filters.get("trust_status") not in _AUTO_PROMOTE_BLOCKED
        ):
            filters["trust_status"] = "verified"
            filters["auto_verified"] = True
        with get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute(
                """
                INSERT INTO sql_memories (
                  id, canonical_question, normalized_question, question_pattern,
                  intent, sql_template, final_sql, question_embedding, sql_embedding,
                  param_schema, parameters,
                  tables, metrics, dimensions, filters, dialect, schema_version,
                  success_count, failure_count, avg_latency_ms, last_result_columns,
                  last_row_count, last_used_at
                )
                VALUES (
                  %s, %s, %s, '', 'sales_trend', %s, %s, %s::vector, %s::vector, '{}'::jsonb, %s::jsonb,
                  %s, %s, %s, %s::jsonb, 'postgresql', 'v1',
                  1, 0, %s, %s, %s, now()
                )
                ON CONFLICT (normalized_question) DO NOTHING
                RETURNING id, canonical_question, normalized_question, question_pattern,
                          intent, sql_template, final_sql, param_schema, parameters,
                          tables, metrics, dimensions, filters, dialect, schema_version,
                          success_count, failure_count, avg_latency_ms, last_result_columns,
                          last_row_count, last_used_at, created_at
                """,
                (
                    str(memory_id),
                    payload.canonical_question,
                    normalized_question,
                    payload.sql_template,
                    payload.final_sql,
                    _vector_literal(payload.question_embedding),
                    _vector_literal(payload.sql_embedding),
                    json.dumps(payload.parameters, ensure_ascii=False),
                    payload.tables,
                    payload.metrics,
                    payload.dimensions,
                    json.dumps(filters, ensure_ascii=False),
                    payload.latency_ms,
                    payload.result_columns,
                    payload.row_count,
                ),
            )
            row = cursor.fetchone()
            return _row_to_memory(row) if row else None

    def _update_success(
        self,
        existing: SqlMemoryRecord,
        payload: SqlMemoryUpsert,
    ) -> SqlMemoryRecord:
        next_success_count = existing.success_count + 1
        next_avg_latency = round(
            ((existing.avg_latency_ms * existing.success_count) + payload.latency_ms)
            / next_success_count
        )
        if existing.trust_status == "verified":
            return self._record_verified_success(
                existing,
                next_success_count=next_success_count,
                next_avg_latency=next_avg_latency,
            )
        with get_connection() as conn:  # noqa: SIM117 - 保持原结构，下方 SQL 使用计算后的 filters
            cursor = conn.cursor()
            cursor.execute(
                """
                UPDATE sql_memories
                SET canonical_question = %s,
                    sql_template = %s,
                    final_sql = %s,
                    question_embedding = COALESCE(%s::vector, question_embedding),
                    sql_embedding = COALESCE(%s::vector, sql_embedding),
                    parameters = %s::jsonb,
                    tables = %s,
                    metrics = %s,
                    dimensions = %s,
                    filters = %s::jsonb,
                    success_count = %s,
                    avg_latency_ms = %s,
                    last_result_columns = %s,
                    last_row_count = %s,
                    last_used_at = now()
                WHERE id = %s
                RETURNING id, canonical_question, normalized_question, question_pattern,
                          intent, sql_template, final_sql, param_schema, parameters,
                          tables, metrics, dimensions, filters, dialect, schema_version,
                          success_count, failure_count, avg_latency_ms, last_result_columns,
                          last_row_count, last_used_at, created_at
                """,
                (
                    payload.canonical_question,
                    payload.sql_template,
                    payload.final_sql,
                    _vector_literal(payload.question_embedding),
                    _vector_literal(payload.sql_embedding),
                    json.dumps(payload.parameters, ensure_ascii=False),
                    payload.tables,
                    payload.metrics,
                    payload.dimensions,
                    json.dumps(
                        self._next_success_filters(existing, payload), ensure_ascii=False
                    ),
                    next_success_count,
                    next_avg_latency,
                    payload.result_columns,
                    payload.row_count,
                    str(existing.id),
                ),
            )
            return _row_to_memory(cursor.fetchone())

    def _next_success_filters(
        self,
        existing: SqlMemoryRecord,
        payload: SqlMemoryUpsert,
    ) -> dict:
        """自动可信状态机（计划 1a）。

        连续成功（auto_verify_streak）满足以下全部条件才累计：
        - 结果列形状与上次一致（result columns 稳定）
        - 上下文指纹（schema + 契约）与已存指纹一致
        streak 达到阈值且当前状态不在人工终态（deprecated/rejected）时，
        自动升级为 verified 并标记 auto_verified=true；任何形状/指纹漂移
        都会把 streak 重置为 1（本次仍是成功，但重新开始累计）。
        """
        filters = _memory_filters(payload)
        current_status = existing.filters.get("trust_status", existing.trust_status)
        previous_streak = int(existing.filters.get("auto_verify_streak", 0) or 0)

        columns_stable = (
            not existing.last_result_columns
            or list(payload.result_columns) == list(existing.last_result_columns)
        )
        stored_fingerprints = existing.filters.get("context_fingerprints") or {}
        incoming_fingerprints = filters.get("context_fingerprints") or {}
        fingerprints_stable = (
            not stored_fingerprints or stored_fingerprints == incoming_fingerprints
        )

        streak = previous_streak + 1 if (columns_stable and fingerprints_stable) else 1
        filters["auto_verify_streak"] = streak

        if current_status in _AUTO_PROMOTE_BLOCKED:
            filters["trust_status"] = current_status
            return filters

        if streak >= settings.memory_auto_verify_threshold:
            filters["trust_status"] = "verified"
            filters["auto_verified"] = True
        else:
            # 未达阈值前保留既有状态（人工 reviewed 不被 executed 覆盖回退）。
            ranking = {"candidate": 0, "executed": 1, "reviewed": 2}
            incoming = str(filters.get("trust_status", "executed"))
            kept = max(
                (current_status, incoming),
                key=lambda status: ranking.get(status, 0),
            )
            filters["trust_status"] = kept
        return filters

    def _record_verified_success(
        self,
        existing: SqlMemoryRecord,
        *,
        next_success_count: int,
        next_avg_latency: int,
    ) -> SqlMemoryRecord:
        """审核后的 SQL 只能由显式信任操作修改，普通成功执行只更新使用统计。"""
        with get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute(
                """
                UPDATE sql_memories
                SET success_count = %s,
                    avg_latency_ms = %s,
                    last_used_at = now()
                WHERE id = %s
                RETURNING id, canonical_question, normalized_question, question_pattern,
                          intent, sql_template, final_sql, param_schema, parameters,
                          tables, metrics, dimensions, filters, dialect, schema_version,
                          success_count, failure_count, avg_latency_ms, last_result_columns,
                          last_row_count, last_used_at, created_at
                """,
                (next_success_count, next_avg_latency, str(existing.id)),
            )
            return _row_to_memory(cursor.fetchone())


def _row_to_memory(row) -> SqlMemoryRecord:
    filters = _json_payload(row[12])
    return SqlMemoryRecord(
        id=row[0],
        canonical_question=row[1],
        normalized_question=row[2],
        question_pattern=row[3],
        intent=row[4],
        sql_template=row[5],
        final_sql=row[6],
        param_schema=_json_payload(row[7]),
        parameters=_json_payload(row[8]),
        tables=list(row[9] or []),
        metrics=list(row[10] or []),
        dimensions=list(row[11] or []),
        filters=filters,
        dialect=row[13],
        schema_version=row[14],
        trust_status=filters.get("trust_status", "reviewed"),
        success_count=row[15],
        failure_count=row[16],
        avg_latency_ms=row[17],
        last_result_columns=list(row[18] or []),
        last_row_count=row[19],
        last_used_at=row[20],
        created_at=row[21],
    )


def _json_payload(value) -> dict:
    if isinstance(value, str):
        return json.loads(value)
    return value or {}


def _vector_literal(vector: list[float] | None) -> str | None:
    if not vector:
        return None
    return "[" + ",".join(f"{float(value):.8f}" for value in vector) + "]"


def _memory_filters(payload: SqlMemoryUpsert) -> dict:
    """SQL Memory 的可信元数据统一落在既有 JSONB，避免平行的未版本化字段。"""
    return {**payload.filters, "trust_status": payload.trust_status}
