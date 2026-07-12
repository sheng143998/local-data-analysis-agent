import json
from datetime import datetime
from uuid import UUID, uuid4

from backend.app.db.connection import get_connection
from backend.app.schemas.auth import AuthSessionInfo, UserProfile


class AuthRepository:
    def create_user(self, *, email: str, display_name: str, password_hash: str, role: str = "analyst") -> UserProfile:
        user_id = uuid4()
        with get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute(
                """
                INSERT INTO app_users (id, email, display_name, password_hash, role)
                VALUES (%s, %s, %s, %s, %s)
                RETURNING id, email, display_name, role, created_at
                """,
                (str(user_id), email, display_name, password_hash, role),
            )
            return _user_profile(cursor.fetchone())

    def get_user_by_email(self, email: str):
        with get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute(
                """
                SELECT id, email, display_name, password_hash, role, status, created_at
                FROM app_users WHERE LOWER(email) = LOWER(%s)
                """,
                (email,),
            )
            return _user_auth_row(cursor.fetchone())

    def get_user(self, user_id: UUID):
        with get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute(
                """
                SELECT id, email, display_name, password_hash, role, status, created_at
                FROM app_users WHERE id = %s
                """,
                (str(user_id),),
            )
            return _user_auth_row(cursor.fetchone())

    def update_password(self, user_id: UUID, password_hash: str) -> None:
        with get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute(
                "UPDATE app_users SET password_hash = %s, updated_at = now() WHERE id = %s",
                (password_hash, str(user_id)),
            )

    def create_session(self, *, user_id: UUID, token_hash: str, csrf_token_hash: str, idle_expires_at: datetime, absolute_expires_at: datetime, user_agent: str, ip_address: str) -> UUID:
        session_id = uuid4()
        with get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute(
                """
                INSERT INTO auth_sessions (
                  id, user_id, token_hash, csrf_token_hash, idle_expires_at,
                  absolute_expires_at, user_agent, ip_address
                ) VALUES (%s, %s, %s, %s, %s, %s, %s, %s)
                """,
                (str(session_id), str(user_id), token_hash, csrf_token_hash, idle_expires_at, absolute_expires_at, user_agent[:512], ip_address[:64]),
            )
        return session_id

    def get_active_session(self, token_hash: str):
        with get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute(
                """
                SELECT s.id, s.user_id, s.csrf_token_hash, s.idle_expires_at, s.absolute_expires_at,
                       u.email, u.display_name, u.role, u.status
                FROM auth_sessions s JOIN app_users u ON u.id = s.user_id
                WHERE s.token_hash = %s AND s.revoked_at IS NULL
                  AND s.idle_expires_at > now() AND s.absolute_expires_at > now()
                """,
                (token_hash,),
            )
            return _session_row(cursor.fetchone())

    def touch_session(self, session_id: UUID, idle_expires_at: datetime) -> None:
        with get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute(
                "UPDATE auth_sessions SET last_seen_at = now(), idle_expires_at = LEAST(%s, absolute_expires_at) WHERE id = %s AND revoked_at IS NULL",
                (idle_expires_at, str(session_id)),
            )

    def revoke_session(self, session_id: UUID) -> None:
        with get_connection() as conn:
            conn.cursor().execute("UPDATE auth_sessions SET revoked_at = now() WHERE id = %s", (str(session_id),))

    def revoke_other_sessions(self, user_id: UUID, current_session_id: UUID) -> None:
        with get_connection() as conn:
            conn.cursor().execute(
                "UPDATE auth_sessions SET revoked_at = now() WHERE user_id = %s AND id <> %s AND revoked_at IS NULL",
                (str(user_id), str(current_session_id)),
            )

    def list_sessions(self, user_id: UUID, current_session_id: UUID | None) -> list[AuthSessionInfo]:
        with get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute(
                """
                SELECT id, created_at, last_seen_at, idle_expires_at, absolute_expires_at
                FROM auth_sessions WHERE user_id = %s AND revoked_at IS NULL
                ORDER BY last_seen_at DESC
                """,
                (str(user_id),),
            )
            return [AuthSessionInfo(id=row[0], created_at=row[1], last_seen_at=row[2], idle_expires_at=row[3], absolute_expires_at=row[4], current=row[0] == current_session_id) for row in cursor.fetchall()]

    def record_event(self, *, user_id: UUID | None, action: str, reason: str = "", metadata: dict | None = None) -> None:
        with get_connection() as conn:
            conn.cursor().execute(
                "INSERT INTO auth_events (id, user_id, action, reason, metadata) VALUES (%s, %s, %s, %s, %s::jsonb)",
                (str(uuid4()), str(user_id) if user_id else None, action, reason, json.dumps(metadata or {}, ensure_ascii=False)),
            )


def _user_profile(row) -> UserProfile:
    return UserProfile(id=row[0], email=row[1], display_name=row[2], role=row[3], created_at=row[4])


def _user_auth_row(row):
    if row is None:
        return None
    return {"id": row[0], "email": row[1], "display_name": row[2], "password_hash": row[3], "role": row[4], "status": row[5], "created_at": row[6]}


def _session_row(row):
    if row is None:
        return None
    return {"id": row[0], "user_id": row[1], "csrf_token_hash": row[2], "idle_expires_at": row[3], "absolute_expires_at": row[4], "email": row[5], "display_name": row[6], "role": row[7], "status": row[8]}
