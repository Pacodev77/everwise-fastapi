# tests/test_comparativa_router.py

import pytest
from fastapi.testclient import TestClient
from app.main import app
from app.routers.auth import SESSION_COOKIE_NAME

client = TestClient(app, follow_redirects=False)

def get_session_cookie(username: str = "director", password: str = "123") -> str:
    client.cookies.clear()
    login_resp = client.post("/login", data={"username": username, "password": password})
    cookie = login_resp.cookies.get(SESSION_COOKIE_NAME)
    client.cookies.set(SESSION_COOKIE_NAME, cookie)
    change_resp = client.post("/change-password", data={
        "new_password": "ValidPassword2026!",
        "confirm_password": "ValidPassword2026!"
    })
    return change_resp.cookies.get(SESSION_COOKIE_NAME)

def test_comparativa_unauthenticated_redirects():
    client.cookies.clear()
    response = client.get("/comparativa")
    assert response.status_code == 307
    assert response.headers["location"] == "/login"

def test_comparativa_renders_for_director():
    cookie = get_session_cookie("director")
    client.cookies.set(SESSION_COOKIE_NAME, cookie)
    response = client.get("/comparativa")
    assert response.status_code == 200
    assert "Comparativa Global Multicampus" in response.text

def test_comparativa_fragment_renders():
    cookie = get_session_cookie("director")
    client.cookies.set(SESSION_COOKIE_NAME, cookie)
    response = client.get("/comparativa/fragments/content?ciclo=2025 - 2026")
    assert response.status_code == 200
    assert "Matriz Comparativa Frente a Frente" in response.text
    assert "Semáforo de Desviación" in response.text

def test_comparativa_rbac_isolation_denied_for_campus_coordinator():
    # El módulo de comparativa global multicampus requiere el rol General (Director General)
    cookie = get_session_cookie("misiones")
    client.cookies.set(SESSION_COOKIE_NAME, cookie)
    resp = client.get("/comparativa")
    assert resp.status_code == 403
    assert "Acceso Restringido" in resp.json()["detail"]
