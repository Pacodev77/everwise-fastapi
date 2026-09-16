# tests/test_preescolar_router.py

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

def test_preescolar_unauthenticated_redirects():
    client.cookies.clear()
    response = client.get("/preescolar")
    assert response.status_code == 307
    assert response.headers["location"] == "/login"

def test_preescolar_renders_authenticated():
    cookie = get_session_cookie("director")
    client.cookies.set(SESSION_COOKIE_NAME, cookie)
    response = client.get("/preescolar")
    assert response.status_code == 200
    assert "Evaluación Cualitativa de Preescolar" in response.text

def test_preescolar_fragment_renders():
    cookie = get_session_cookie("director")
    client.cookies.set(SESSION_COOKIE_NAME, cookie)
    response = client.get("/preescolar/fragments/content?ciclo=2025 - 2026&campus=Misiones")
    assert response.status_code == 200
    assert "Rúbrica Cualitativa por Campo Formativo" in response.text
    assert "Desarrollo Socioemocional" in response.text

def test_preescolar_rbac_isolation_campus_coordinator_allowed():
    cookie = get_session_cookie("misiones")
    client.cookies.set(SESSION_COOKIE_NAME, cookie)
    resp = client.get("/preescolar")
    assert resp.status_code == 200

def test_preescolar_rbac_isolation_campus_cross_access_prevented():
    """
    Confirma que un coordinador del campus Misiones que intenta consultar la evaluación de Nuevo Sur
    es forzado a ver únicamente los datos de su propio campus ('Misiones') vía resolve_campus_for_user.
    """
    cookie = get_session_cookie("misiones")
    client.cookies.set(SESSION_COOKIE_NAME, cookie)
    # El usuario 'misiones' intenta pasar campus=Nuevo Sur
    resp = client.get("/preescolar/fragments/content?campus=Nuevo Sur")
    assert resp.status_code == 200
    # Verifica que el campus resuelto en el HTML es 'Misiones' y NO 'Nuevo Sur'
    assert "Misiones" in resp.text
    assert "Nuevo Sur" not in resp.text
