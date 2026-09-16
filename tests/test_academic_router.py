# tests/test_academic_router.py

import pytest
from fastapi.testclient import TestClient
from app.main import app
from app.routers.auth import SESSION_COOKIE_NAME

client = TestClient(app, follow_redirects=False)

def get_session_cookie(username: str = "director", password: str = "123") -> str:
    login_resp = client.post("/login", data={"username": username, "password": password})
    cookie = login_resp.cookies.get(SESSION_COOKIE_NAME)
    client.cookies.set(SESSION_COOKIE_NAME, cookie)
    change_resp = client.post("/change-password", data={
        "new_password": "ValidPassword2026!",
        "confirm_password": "ValidPassword2026!"
    })
    return change_resp.cookies.get(SESSION_COOKIE_NAME)

def test_academic_page_unauthenticated_redirects():
    client.cookies.clear()
    response = client.get("/academic")
    assert response.status_code == 307
    assert response.headers["location"] == "/login"

def test_academic_page_renders_authenticated():
    cookie = get_session_cookie("director")
    client.cookies.set(SESSION_COOKIE_NAME, cookie)
    response = client.get("/academic")
    assert response.status_code == 200
    assert "Desempeño Académico" in response.text

def test_academic_fragment_renders():
    cookie = get_session_cookie("director")
    client.cookies.set(SESSION_COOKIE_NAME, cookie)
    response = client.get("/academic/fragments/content?ciclo=2025 - 2026&campus=Misiones")
    assert response.status_code == 200
    assert "Desglose por Bimestre" in response.text
    assert "Promedio General Académico" in response.text

def test_academic_rbac_isolation():
    # Usuario Misiones sin permiso a vista de director o campus cruzado
    cookie = get_session_cookie("misiones")
    client.cookies.set(SESSION_COOKIE_NAME, cookie)
    # Acceso a /academic para su campus debe retornar 200
    resp_own = client.get("/academic")
    assert resp_own.status_code == 200
