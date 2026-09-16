# tests/test_auth_router.py

import pytest
from fastapi import APIRouter, Depends, Request
from fastapi.testclient import TestClient
from app.main import app
from app.routers.auth import SESSION_COOKIE_NAME, require_role, get_current_user
from app.models.user import UserBase

# Router de prueba para verificar RBAC
test_router = APIRouter(prefix="/test-campus", tags=["TestRBAC"])

@test_router.get("/nuevosur")
async def dummy_nuevosur_endpoint(user: UserBase = Depends(require_role(["Nuevo Sur"]))):
    return {"message": "Bienvenido a Nuevo Sur"}

app.include_router(test_router)

client = TestClient(app, follow_redirects=False)

def test_login_page_renders():
    response = client.get("/login")
    assert response.status_code == 200
    assert "Everwise" in response.text
    assert "Usuario Corporativo" in response.text

def test_login_invalid_credentials():
    response = client.post("/login", data={"username": "director", "password": "wrongpassword"})
    assert response.status_code == 401
    assert "Credenciales incorrectas" in response.text

def test_login_success_and_cookie_issued():
    response = client.post("/login", data={"username": "director", "password": "123"})
    assert response.status_code == 303
    assert response.headers["location"] == "/dashboard"
    assert SESSION_COOKIE_NAME in response.cookies

def test_session_cookie_flags():
    """Confirma que la cookie de sesión emite las banderas HttpOnly y SameSite=Lax."""
    response = client.post("/login", data={"username": "director", "password": "123"})
    cookie_header = response.headers.get("set-cookie", "")
    assert "HttpOnly" in cookie_header or "httponly" in cookie_header.lower()
    assert "samesite=lax" in cookie_header.lower()

def test_logout_clears_cookie():
    login_resp = client.post("/login", data={"username": "director", "password": "123"})
    cookie = login_resp.cookies.get(SESSION_COOKIE_NAME)

    client.cookies.set(SESSION_COOKIE_NAME, cookie)
    logout_resp = client.get("/logout")
    assert logout_resp.status_code == 303
    assert logout_resp.headers["location"] == "/login"

def test_rbac_isolation_misiones_denied_nuevosur():
    """
    Confirma explícitamente que un usuario con rol 'Misiones'
    recibe un error HTTP 403 Forbidden al intentar acceder a una ruta de 'Nuevo Sur'.
    """
    # 1. Autenticar como usuario 'misiones'
    login_resp = client.post("/login", data={"username": "misiones", "password": "123"})
    cookie = login_resp.cookies.get(SESSION_COOKIE_NAME)

    # 2. Intentar acceder a ruta protegida de 'Nuevo Sur'
    client.cookies.set(SESSION_COOKIE_NAME, cookie)
    resp = client.get("/test-campus/nuevosur")
    
    assert resp.status_code == 403
    assert "Acceso Restringido" in resp.json()["detail"]
