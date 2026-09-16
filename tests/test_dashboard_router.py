# tests/test_dashboard_router.py

import pytest
from fastapi.testclient import TestClient
from app.main import app
from app.routers.auth import SESSION_COOKIE_NAME

client = TestClient(app, follow_redirects=False)

@pytest.fixture
def auth_cookie():
    response = client.post("/login", data={"username": "director", "password": "123"})
    return response.cookies.get(SESSION_COOKIE_NAME)

def test_dashboard_unauthenticated_redirects():
    response = client.get("/dashboard")
    assert response.status_code == 307
    assert response.headers["location"] == "/login"

def test_dashboard_authenticated_success(auth_cookie):
    client.cookies.set(SESSION_COOKIE_NAME, auth_cookie)
    response = client.get("/dashboard")
    assert response.status_code == 200
    assert "Resumen Data 2025 - 2026" in response.text

def test_reproducir_solucion_bug_selector_ciclo_escolar(auth_cookie):
    """
    Prueba automatizada que reproduce la interacción del selector de Ciclo Escolar en la misma sesión HTTP.
    Verifica que al cambiar el ciclo, los datos devueltos por el fragmento HTMX cambian
    de manera determinista y no retienen valores anteriores en memoria.
    """
    client.cookies.set(SESSION_COOKIE_NAME, auth_cookie)

    # 1. Petición inicial para Ciclo 2025 - 2026
    resp1 = client.get("/dashboard/fragments/kpis?ciclo=2025 - 2026")
    assert resp1.status_code == 200
    assert "2025 - 2026" in resp1.text
    assert "87.8%" in resp1.text

    # 2. Cambio inmediato en la misma sesión a Ciclo 2026 - 2027
    resp2 = client.get("/dashboard/fragments/kpis?ciclo=2026 - 2027")
    assert resp2.status_code == 200
    assert "2026 - 2027" in resp2.text
    assert "84.2%" in resp2.text
    assert "87.8%" not in resp2.text  # Garantiza que el valor anterior NO se quedó en memoria

    # 3. Retorno a Ciclo 2024 - 2025
    resp3 = client.get("/dashboard/fragments/kpis?ciclo=2024 - 2025")
    assert resp3.status_code == 200
    assert "2024 - 2025" in resp3.text

def test_htmx_composite_chart_fragment(auth_cookie):
    client.cookies.set(SESSION_COOKIE_NAME, auth_cookie)
    response = client.get("/dashboard/fragments/composite_chart?ciclo=2025 - 2026")
    assert response.status_code == 200
    assert "Índice Compuesto Institucional" in response.text
    assert "Misiones" in response.text

def test_htmx_ai_insights_fragment(auth_cookie):
    client.cookies.set(SESSION_COOKIE_NAME, auth_cookie)
    response = client.get("/dashboard/fragments/ai_insights?ciclo=2025 - 2026")
    assert response.status_code == 200
    assert "Gemini AI" in response.text
    assert "Qué Mantener" in response.text
