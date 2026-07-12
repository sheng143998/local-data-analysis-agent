import json
from uuid import UUID, uuid4

from backend.app.db.connection import get_connection
from backend.app.schemas.long_term_memory import LongTermMemory, RememberedPreference


class LongTermMemoryRepository:
    def list_active(self, user_id: UUID) -> list[LongTermMemory]:
        subject_id = self._find_subject_id(user_id)
        if subject_id is None:
            return []
        with get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute(
                """
                SELECT id, memory_key, category, value, status, version, created_at, updated_at
                FROM long_term_memories WHERE subject_id = %s AND status = 'active'
                ORDER BY updated_at DESC
                """,
                (str(subject_id),),
            )
            return [_memory(row) for row in cursor.fetchall()]

    def remember(self, user_id: UUID, preference: RememberedPreference, conversation_id: UUID | None = None) -> LongTermMemory:
        subject_id = self._ensure_subject(user_id)
        with get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute(
                """
                SELECT id, value, version FROM long_term_memories
                WHERE subject_id = %s AND memory_key = %s AND status = 'active'
                """,
                (str(subject_id), preference.memory_key),
            )
            current = cursor.fetchone()
            if current and _json(current[1]) == preference.value:
                return self._get_memory(UUID(str(current[0])))
            version = int(current[2]) + 1 if current else 1
            if current:
                cursor.execute("UPDATE long_term_memories SET status = 'superseded', updated_at = now() WHERE id = %s", (str(current[0]),))
                self._event(cursor, subject_id, UUID(str(current[0])), "superseded", "explicit_preference_replaced")
            memory_id = uuid4()
            cursor.execute(
                """
                INSERT INTO long_term_memories (id, subject_id, memory_key, category, value, version, source_conversation_id)
                VALUES (%s, %s, %s, %s, %s::jsonb, %s, %s)
                """,
                (str(memory_id), str(subject_id), preference.memory_key, preference.category, json.dumps(preference.value, ensure_ascii=False), version, str(conversation_id) if conversation_id else None),
            )
            self._event(cursor, subject_id, memory_id, "created", "explicit_preference")
        return self._get_memory(memory_id)

    def revoke(self, user_id: UUID, memory_key: str) -> bool:
        subject_id = self._find_subject_id(user_id)
        if subject_id is None:
            return False
        with get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute(
                """
                UPDATE long_term_memories SET status = 'revoked', revoked_at = now(), updated_at = now()
                WHERE subject_id = %s AND memory_key = %s AND status = 'active'
                RETURNING id
                """,
                (str(subject_id), memory_key),
            )
            row = cursor.fetchone()
            if not row:
                return False
            self._event(cursor, subject_id, UUID(str(row[0])), "revoked", "explicit_forget")
            return True

    def _ensure_subject(self, user_id: UUID) -> UUID:
        with get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute(
                """
                INSERT INTO memory_subjects (id, app_user_id) VALUES (%s, %s)
                ON CONFLICT (app_user_id) DO UPDATE SET updated_at = now()
                RETURNING id
                """,
                (str(uuid4()), str(user_id)),
            )
            return UUID(str(cursor.fetchone()[0]))

    def _find_subject_id(self, user_id: UUID) -> UUID | None:
        with get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute("SELECT id FROM memory_subjects WHERE app_user_id = %s", (str(user_id),))
            row = cursor.fetchone()
            return UUID(str(row[0])) if row else None

    def _get_memory(self, memory_id: UUID) -> LongTermMemory:
        with get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute("SELECT id, memory_key, category, value, status, version, created_at, updated_at FROM long_term_memories WHERE id = %s", (str(memory_id),))
            return _memory(cursor.fetchone())

    @staticmethod
    def _event(cursor, subject_id: UUID, memory_id: UUID, action: str, reason: str) -> None:
        cursor.execute(
            "INSERT INTO long_term_memory_events (id, memory_id, subject_id, action, reason) VALUES (%s, %s, %s, %s, %s)",
            (str(uuid4()), str(memory_id), str(subject_id), action, reason),
        )


def _memory(row) -> LongTermMemory:
    return LongTermMemory(id=row[0], memory_key=row[1], category=row[2], value=_json(row[3]), status=row[4], version=row[5], created_at=row[6], updated_at=row[7])


def _json(value) -> dict[str, str]:
    if isinstance(value, str):
        value = json.loads(value)
    return {str(key): str(item) for key, item in (value or {}).items()}
