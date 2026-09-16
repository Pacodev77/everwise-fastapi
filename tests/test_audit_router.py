# tests/test_audit_router.py

# pyrefly: ignore [missing-import]
from fastapi.testclient import TestClient
from app.main import app
from app.routers.auth import SESSION_COOKIE_NAME
from app.services.data_repository import DataRepository
from app.models.audit import AuditLogEntry

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

def test_audit_page_unauthenticated_redirects():
    client.cookies.clear()
    response = client.get("/audit")
    assert response.status_code == 307
    assert response.headers["location"] == "/login"

def test_audit_page_renders():
    cookie = get_session_cookie("director")
    client.cookies.set(SESSION_COOKIE_NAME, cookie)
    response = client.get("/audit")
    assert response.status_code == 200
    assert "Bitácora CRM" in response.text

def test_audit_table_fragment_renders():
    cookie = get_session_cookie("director")
    client.cookies.set(SESSION_COOKIE_NAME, cookie)
    response = client.get("/audit/fragments/table")
    assert response.status_code == 200
    assert "Registro de Eventos" in response.text or "styled-table" in response.text

def test_audit_export_csv_role_filtered():
    # 1. Sembrar registros de prueba para Misiones y Nuevo Sur
    repo = DataRepository()
    repo.add_audit_log(AuditLogEntry(usuario="misiones", accion="TEST_MISIONES", detalle="Evento Misiones", campus="Misiones"))
    repo.add_audit_log(AuditLogEntry(usuario="nuevosur", accion="TEST_NUEVOSUR", detalle="Evento Nuevo Sur", campus="Nuevo Sur"))

    # 2. Exportar como coordinador de Misiones
    misiones_cookie = get_session_cookie("misiones")
    client.cookies.set(SESSION_COOKIE_NAME, misiones_cookie)
    misiones_export = client.get("/audit/export")

    assert misiones_export.status_code == 200
    assert "text/csv" in misiones_export.headers["content-type"]
    csv_text = misiones_export.text
    assert "TEST_MISIONES" in csv_text
    # El coordinador de Misiones NO debe poder exportar ni ver registros de Nuevo Sur
    assert "TEST_NUEVOSUR" not in csv_text

    # 3. Exportar como Director General (General)
    director_cookie = get_session_cookie("director")
    client.cookies.set(SESSION_COOKIE_NAME, director_cookie)
    director_export = client.get("/audit/export")

    assert director_export.status_code == 200
    dir_csv_text = director_export.text
    assert "TEST_MISIONES" in dir_csv_text
    assert "TEST_NUEVOSUR" in dir_csv_text

def test_audit_rbac_isolation():
    misiones_cookie = get_session_cookie("misiones")
    client.cookies.set(SESSION_COOKIE_NAME, misiones_cookie)
    resp = client.get("/audit")
    assert resp.status_code == 200
