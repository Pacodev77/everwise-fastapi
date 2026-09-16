# tests/test_auth_router.py

import pytest
from fastapi.testclient import TestClient
from app.main import app
from app.routers.auth import SESSION_COOKIE_NAME

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

def test_logout_clears_cookie():
    # Login first
    login_resp = client.post("/login", data={"username": "director", "password": "123"})
    cookie = login_resp.cookies.get(SESSION_COOKIE_NAME)

    # Logout
    client.cookies.set(SESSION_COOKIE_NAME, cookie)
    logout_resp = client.get("/logout")
    assert logout_resp.status_code == 303
    assert logout_resp.headers["location"] == "/login"
