from fastapi import APIRouter, Depends, Request, Response
from uuid import UUID

from backend.app.api.dependencies import get_current_principal, require_csrf
from backend.app.schemas.auth import AuthPrincipal, AuthResponse, AuthSessionInfo, LoginRequest, PasswordChangeRequest, RegisterRequest
from backend.app.services.auth_service import AuthService


router = APIRouter(prefix="/auth", tags=["auth"])
auth_service = AuthService()


@router.post("/register", response_model=AuthResponse)
def register(payload: RegisterRequest, request: Request, response: Response) -> AuthResponse:
    return auth_service.register(payload, request, response)


@router.post("/login", response_model=AuthResponse)
def login(payload: LoginRequest, request: Request, response: Response) -> AuthResponse:
    return auth_service.login(payload, request, response)


@router.get("/me", response_model=AuthResponse)
def me(principal: AuthPrincipal = Depends(get_current_principal)) -> AuthResponse:
    return auth_service.me(principal)


@router.post("/logout", status_code=204, dependencies=[Depends(require_csrf)])
def logout(response: Response, principal: AuthPrincipal = Depends(get_current_principal)) -> Response:
    auth_service.logout(principal, response)
    response.status_code = 204
    return response


@router.post("/password", status_code=204, dependencies=[Depends(require_csrf)])
def change_password(payload: PasswordChangeRequest, principal: AuthPrincipal = Depends(get_current_principal)) -> None:
    auth_service.change_password(principal, payload)


@router.get("/sessions", response_model=list[AuthSessionInfo])
def list_sessions(principal: AuthPrincipal = Depends(get_current_principal)) -> list[AuthSessionInfo]:
    return auth_service.repository.list_sessions(principal.id, principal.session_id)


@router.delete("/sessions/{session_id}", status_code=204, dependencies=[Depends(require_csrf)])
def revoke_session(session_id: UUID, response: Response, principal: AuthPrincipal = Depends(get_current_principal)) -> Response:
    auth_service.revoke_session(principal, session_id)
    response.status_code = 204
    return response
