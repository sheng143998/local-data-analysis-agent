from typing import Callable

from fastapi import Depends, Header, HTTPException, Request

from backend.app.core.config import settings
from backend.app.schemas.auth import AuthPrincipal
from backend.app.services.auth_service import get_principal_from_session, verify_csrf_token


def _resolve_session(request: Request):
    """每个请求只做一次会话查库，结果缓存在 request.state 供各依赖复用。

    此前 get_current_principal 与 require_csrf 各查一次，带 CSRF 保护的写接口
    每次要付两趟 auth_sessions JOIN app_users 查询。
    """
    if not hasattr(request.state, "auth_session"):
        request.state.auth_session = get_principal_from_session(
            request.cookies.get(settings.auth_cookie_name)
        )
    return request.state.auth_session


def get_current_principal(request: Request) -> AuthPrincipal:
    if not settings.auth_required:
        return AuthPrincipal(
            id=settings.development_principal_id,
            email=settings.auth_dev_user_email,
            display_name="Local Administrator",
            role="admin",
            is_development_principal=True,
        )
    session = _resolve_session(request)
    if session is None:
        raise HTTPException(status_code=401, detail="请先登录后再继续")
    return session[0]


def require_csrf(request: Request, x_csrf_token: str | None = Header(default=None, alias="X-CSRF-Token")) -> None:
    if not settings.auth_required:
        return
    session = _resolve_session(request)
    if session is None or not verify_csrf_token(x_csrf_token, session[1]):
        raise HTTPException(status_code=403, detail="CSRF 校验失败，请刷新页面后重试")


def require_role(*roles: str) -> Callable:
    def dependency(principal: AuthPrincipal = Depends(get_current_principal)) -> AuthPrincipal:
        if principal.role not in roles:
            raise HTTPException(status_code=403, detail="当前账号没有执行该操作的权限")
        return principal

    return dependency
