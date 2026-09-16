# tests/test_clima_disciplina_router.py

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

def test_clima_page_unauthenticated_redirects():
    client.cookies.clear()
    response = client.get("/clima")
    assert response.status_code == 307
    assert response.headers["location"] == "/login"

def test_disciplina_page_unauthenticated_redirects():
    client.cookies.clear()
    response = client.get("/disciplina")
    assert response.status_code == 307
    assert response.headers["location"] == "/login"

def test_clima_page_renders():
    cookie = get_session_cookie("director")
    client.cookies.set(SESSION_COOKIE_NAME, cookie)
    response = client.get("/clima")
    assert response.status_code == 200
    assert "Clima Escolar & Ambiente" in response.text

def test_disciplina_page_renders():
    cookie = get_session_cookie("director")
    client.cookies.set(SESSION_COOKIE_NAME, cookie)
    response = client.get("/disciplina")
    assert response.status_code == 200
    assert "Seguimiento Disciplinario" in response.text

def test_clima_disciplina_rbac_isolation():
    cookie = get_session_cookie("misiones")
    client.cookies.set(SESSION_COOKIE_NAME, cookie)
    resp_clima = client.get("/clima")
    assert resp_clima.status_code == 200
    resp_disc = client.get("/disciplina")
    assert resp_disc.status_code == 200
