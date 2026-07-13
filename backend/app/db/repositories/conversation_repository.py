import json
from datetime import datetime, timedelta, timezone
from uuid import UUID

from backend.app.core.config import settings
from backend.app.db.connection import get_connection
from backend.app.schemas.conversation import ConversationState


class ConversationRepository:
    """会话状态的持久化副本，确保 Redis 不可用时仍可恢复用户历史。"""

    def get(self, conversation_id: UUID) -> ConversationState | None:
        with get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute(
                "SELECT state FROM conversation_states WHERE id = %s AND expires_at > now()",
                (str(conversation_id),),
            )
            row = cursor.fetchone()
        return _state(row[0]) if row else None

    def save(self, state: ConversationState) -> None:
        expires_at = datetime.now(timezone.utc) + timedelta(hours=settings.conversation_retention_hours)
        payload = json.dumps(state.model_dump(mode="json"), ensure_ascii=False)
        with get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute(
                """
                INSERT INTO conversation_states (
                  id, owner_id, title, status, state, created_at, updated_at, expires_at
                ) VALUES (%s, %s, %s, %s, %s::jsonb, %s, %s, %s)
                ON CONFLICT (id) DO UPDATE SET
                  owner_id = EXCLUDED.owner_id,
                  title = EXCLUDED.title,
                  status = EXCLUDED.status,
                  state = EXCLUDED.state,
                  updated_at = EXCLUDED.updated_at,
                  expires_at = EXCLUDED.expires_at
                """,
                (
                    str(state.id),
                    str(state.owner_id) if state.owner_id else None,
                    state.title,
                    state.status,
                    payload,
                    state.created_at,
                    state.updated_at,
                    expires_at,
                ),
            )

    def list_for_owner(
        self, owner_id: UUID | None, limit: int, cursor: tuple[datetime, UUID] | None = None
    ) -> list[ConversationState]:
        cursor_clause = ""
        cursor_params: tuple = ()
        if cursor is not None:
            updated_at, conversation_id = cursor
            cursor_clause = " AND (updated_at < %s OR (updated_at = %s AND id < %s))"
            cursor_params = (updated_at, updated_at, str(conversation_id))
        with get_connection() as conn:
            cursor = conn.cursor()
            if owner_id is None:
                cursor.execute(
                    "SELECT state FROM conversation_states WHERE owner_id IS NULL AND expires_at > now()"
                    + cursor_clause
                    + " ORDER BY updated_at DESC, id DESC LIMIT %s",
                    (*cursor_params, limit),
                )
            else:
                cursor.execute(
                    "SELECT state FROM conversation_states WHERE owner_id = %s AND expires_at > now()"
                    + cursor_clause
                    + " ORDER BY updated_at DESC, id DESC LIMIT %s",
                    (str(owner_id), *cursor_params, limit),
                )
            rows = cursor.fetchall()
        return [_state(row[0]) for row in rows]

    def claim_development_conversations(self, owner_id: UUID) -> int:
        """管理员显式迁移本机匿名会话，禁止在普通登录流程中自动执行。"""
        with get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute(
                """
                UPDATE conversation_states
                SET owner_id = %s,
                    state = jsonb_set(state, '{owner_id}', to_jsonb(%s::text), true),
                    updated_at = now()
                WHERE owner_id IS NULL AND expires_at > now()
                """,
                (str(owner_id), str(owner_id)),
            )
            return cursor.rowcount


def _state(value) -> ConversationState:
    if isinstance(value, str):
        value = json.loads(value)
    return ConversationState.model_validate(value)
