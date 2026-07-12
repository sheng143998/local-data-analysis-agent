from uuid import uuid4

from fastapi.testclient import TestClient

from backend.app.core.config import settings
from backend.app.db.repositories.auth_repository import AuthRepository
from backend.app.main import app


def _enable_auth(monkeypatch) -> None:
    monkeypatch.setattr(settings, "auth_required", True)
    monkeypatch.setattr(settings, "auth_allow_self_registration", True)


def test_register_me_and_csrf_protected_logout(monkeypatch) -> None:
    _enable_auth(monkeypatch)
    client = TestClient(app)
    email = f"auth-{uuid4().hex}@example.com"

    register = client.post("/api/auth/register", json={"email": email, "display_name": "Auth Test", "password": "correct horse battery staple"})

    assert register.status_code == 200
    assert register.json()["user"]["email"] == email
    assert "password" not in register.text
    stored = AuthRepository().get_user_by_email(email)
    assert stored is not None
    assert stored["password_hash"] != "correct horse battery staple"
    assert stored["password_hash"].startswith("$argon2")
    assert client.get("/api/auth/me").status_code == 200
    assert client.post("/api/auth/logout").status_code == 403

    csrf = client.cookies.get(settings.auth_csrf_cookie_name)
    logout = client.post("/api/auth/logout", headers={"X-CSRF-Token": csrf})
    assert logout.status_code == 204
    assert client.get("/api/auth/me").status_code == 401


def test_analyst_cannot_access_admin_run_history(monkeypatch) -> None:
    _enable_auth(monkeypatch)
    client = TestClient(app)
    email = f"analyst-{uuid4().hex}@example.com"
    response = client.post("/api/auth/register", json={"email": email, "display_name": "Analyst", "password": "correct horse battery staple"})
    assert response.status_code == 200
    assert client.get("/api/runs").status_code == 403


def test_unauthenticated_analyze_is_rejected(monkeypatch) -> None:
    _enable_auth(monkeypatch)
    client = TestClient(app)
    response = client.post("/api/analyze", json={"question": "最近30天销售额"})
    assert response.status_code == 401


def test_user_can_revoke_another_own_session(monkeypatch) -> None:
    _enable_auth(monkeypatch)
    first_client = TestClient(app)
    second_client = TestClient(app)
    email = f"session-{uuid4().hex}@example.com"
    password = "correct horse battery staple"
    assert first_client.post("/api/auth/register", json={"email": email, "display_name": "Session Test", "password": password}).status_code == 200
    assert second_client.post("/api/auth/login", json={"email": email, "password": password}).status_code == 200
    sessions = first_client.get("/api/auth/sessions").json()
    other_session = next(item for item in sessions if not item["current"])

    csrf = first_client.cookies.get(settings.auth_csrf_cookie_name)
    response = first_client.delete(f"/api/auth/sessions/{other_session['id']}", headers={"X-CSRF-Token": csrf})
    assert response.status_code == 204
    assert second_client.get("/api/auth/me").status_code == 401


def test_login_rate_limit_uses_development_fallback_when_redis_is_unavailable(monkeypatch) -> None:
    _enable_auth(monkeypatch)
    monkeypatch.setattr(settings, "auth_login_rate_limit_per_15_minutes", 1)
    owner_client = TestClient(app)
    login_client = TestClient(app)
    email = f"rate-{uuid4().hex}@example.com"
    password = "correct horse battery staple"
    assert owner_client.post("/api/auth/register", json={"email": email, "display_name": "Rate Test", "password": password}).status_code == 200
    assert login_client.post("/api/auth/login", json={"email": email, "password": password}).status_code == 200
    assert login_client.post("/api/auth/login", json={"email": email, "password": password}).status_code == 429
