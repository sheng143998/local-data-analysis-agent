from datetime import datetime, timedelta, timezone
from uuid import UUID

from fastapi import HTTPException, Request, Response

from backend.app.core.config import settings
from backend.app.core.auth_rate_limiter import auth_rate_limiter
from backend.app.core.security import hash_password, hash_token, new_secret_token, tokens_match, verify_password
from backend.app.db.repositories.auth_repository import AuthRepository
from backend.app.schemas.auth import AuthPrincipal, AuthResponse, LoginRequest, PasswordChangeRequest, RegisterRequest, UserProfile


class AuthService:
    def __init__(self, repository: AuthRepository | None = None) -> None:
        self.repository = repository or AuthRepository()

    def register(self, payload: RegisterRequest, request: Request, response: Response) -> AuthResponse:
        if not settings.auth_allow_self_registration:
            raise HTTPException(status_code=403, detail="当前环境未开放自助注册")
        email = str(payload.email).strip().lower()
        auth_rate_limiter.enforce("register", request, email, settings.auth_register_rate_limit_per_hour, 60 * 60)
        if self.repository.get_user_by_email(email) is not None:
            self.repository.record_event(user_id=None, action="register_rejected", reason="duplicate_email")
            raise HTTPException(status_code=409, detail="该邮箱无法注册")
        user = self.repository.create_user(email=email, display_name=payload.display_name.strip(), password_hash=hash_password(payload.password))
        self.repository.record_event(user_id=user.id, action="register")
        return self._create_session(user, request, response)

    def login(self, payload: LoginRequest, request: Request, response: Response) -> AuthResponse:
        email = str(payload.email).strip().lower()
        auth_rate_limiter.enforce("login", request, email, settings.auth_login_rate_limit_per_15_minutes, 15 * 60)
        user = self.repository.get_user_by_email(email)
        if user is None or user["status"] != "active" or not verify_password(payload.password, user["password_hash"]):
            self.repository.record_event(user_id=user["id"] if user else None, action="login_rejected", reason="invalid_credentials")
            raise HTTPException(status_code=401, detail="邮箱或密码错误")
        profile = UserProfile(id=user["id"], email=user["email"], display_name=user["display_name"], role=user["role"], created_at=user["created_at"])
        self.repository.record_event(user_id=profile.id, action="login")
        return self._create_session(profile, request, response)

    def logout(self, principal: AuthPrincipal, response: Response) -> None:
        if principal.session_id:
            self.repository.revoke_session(principal.session_id)
            self.repository.record_event(user_id=principal.id, action="logout")
        self._clear_cookies(response)

    def me(self, principal: AuthPrincipal, csrf_token: str | None = None) -> AuthResponse:
        if principal.is_development_principal:
            return AuthResponse(
                user=UserProfile(
                    id=principal.id,
                    email=principal.email,
                    display_name=principal.display_name,
                    role=principal.role,
                    created_at=datetime(1970, 1, 1, tzinfo=timezone.utc),
                ),
                csrf_token="",
            )
        user = self.repository.get_user(principal.id)
        if user is None:
            raise HTTPException(status_code=401, detail="登录状态已失效")
        profile = UserProfile(id=user["id"], email=user["email"], display_name=user["display_name"], role=user["role"], created_at=user["created_at"])
        return AuthResponse(user=profile, csrf_token=csrf_token or "")

    def change_password(self, principal: AuthPrincipal, payload: PasswordChangeRequest) -> None:
        user = self.repository.get_user(principal.id)
        if user is None or not verify_password(payload.current_password, user["password_hash"]):
            raise HTTPException(status_code=400, detail="当前密码不正确")
        self.repository.update_password(principal.id, hash_password(payload.new_password))
        if principal.session_id:
            self.repository.revoke_other_sessions(principal.id, principal.session_id)
        self.repository.record_event(user_id=principal.id, action="password_changed")

    def revoke_session(self, principal: AuthPrincipal, session_id: UUID) -> None:
        sessions = self.repository.list_sessions(principal.id, principal.session_id)
        if not any(session.id == session_id for session in sessions):
            raise HTTPException(status_code=404, detail="会话不存在")
        self.repository.revoke_session(session_id)
        self.repository.record_event(user_id=principal.id, action="session_revoked")

    def _create_session(self, user: UserProfile, request: Request, response: Response) -> AuthResponse:
        session_token, csrf_token = new_secret_token(), new_secret_token()
        now = datetime.now(timezone.utc)
        absolute_expires_at = now + timedelta(days=settings.auth_session_absolute_days)
        idle_expires_at = min(now + timedelta(hours=settings.auth_session_idle_hours), absolute_expires_at)
        self.repository.create_session(
            user_id=user.id,
            token_hash=hash_token(session_token),
            csrf_token_hash=hash_token(csrf_token),
            idle_expires_at=idle_expires_at,
            absolute_expires_at=absolute_expires_at,
            user_agent=request.headers.get("user-agent", ""),
            ip_address=request.client.host if request.client else "",
        )
        self._set_cookies(response, session_token, csrf_token)
        return AuthResponse(user=user, csrf_token=csrf_token)

    def _set_cookies(self, response: Response, session_token: str, csrf_token: str) -> None:
        max_age = settings.auth_session_absolute_days * 24 * 60 * 60
        response.set_cookie(settings.auth_cookie_name, session_token, max_age=max_age, httponly=True, secure=settings.auth_cookie_secure, samesite="lax", path="/")
        response.set_cookie(settings.auth_csrf_cookie_name, csrf_token, max_age=max_age, httponly=False, secure=settings.auth_cookie_secure, samesite="lax", path="/")

    def _clear_cookies(self, response: Response) -> None:
        response.delete_cookie(settings.auth_cookie_name, path="/", secure=settings.auth_cookie_secure, samesite="lax")
        response.delete_cookie(settings.auth_csrf_cookie_name, path="/", secure=settings.auth_cookie_secure, samesite="lax")


def get_principal_from_session(token: str | None) -> tuple[AuthPrincipal, str] | None:
    if not token:
        return None
    session = AuthRepository().get_active_session(hash_token(token))
    if session is None or session["status"] != "active":
        return None
    AuthRepository().touch_session(session["id"], datetime.now(timezone.utc) + timedelta(hours=settings.auth_session_idle_hours))
    return (AuthPrincipal(id=session["user_id"], email=session["email"], display_name=session["display_name"], role=session["role"], session_id=session["id"]), session["csrf_token_hash"])


def verify_csrf_token(token: str | None, csrf_token_hash: str) -> bool:
    return bool(token and tokens_match(token, csrf_token_hash))
