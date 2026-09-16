# tests/test_upload_router.py

import io
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

def test_upload_page_renders():
    cookie = get_session_cookie("director")
    client.cookies.set(SESSION_COOKIE_NAME, cookie)
    response = client.get("/upload")
    assert response.status_code == 200
    assert "Ingesta Masiva" in response.text
    assert "Calificaciones Académicas" in response.text

def test_upload_valid_csv_academic():
    cookie = get_session_cookie("director")
    client.cookies.set(SESSION_COOKIE_NAME, cookie)

    csv_content = b"MATRICULA,ALUMNO,Grupo,Language Arts,Matem\xc3\xa1ticas,Espa\xc3\xb1ol,Nivel\n101,Juan Perez,1A,9.0,8.5,9.2,Primaria\n"
    files = {"file": ("calificaciones.csv", io.BytesIO(csv_content), "text/csv")}
    data = {"ciclo": "2025 - 2026", "campus": "Misiones"}

    response = client.post("/upload/academic", files=files, data=data, headers={"HX-Request": "true"})
    assert response.status_code == 200
    assert "Operación Exitosa" in response.text
    assert "calificaciones.csv" in response.text

def test_upload_invalid_mime_type():
    cookie = get_session_cookie("director")
    client.cookies.set(SESSION_COOKIE_NAME, cookie)

    fake_content = b"Content-Type: executable code"
    files = {"file": ("malicious.exe", io.BytesIO(fake_content), "application/x-msdownload")}
    data = {"ciclo": "2025 - 2026", "campus": "Misiones"}

    response = client.post("/upload/academic", files=files, data=data, headers={"HX-Request": "true"})
    assert response.status_code == 200
    assert "Extensión" in response.text or "no permitida" in response.text or "Error" in response.text

def test_upload_exceeds_max_size():
    cookie = get_session_cookie("director")
    client.cookies.set(SESSION_COOKIE_NAME, cookie)

    large_content = b"A" * (16 * 1024 * 1024)
    files = {"file": ("large_file.csv", io.BytesIO(large_content), "text/csv")}
    data = {"ciclo": "2025 - 2026", "campus": "Misiones"}

    response = client.post("/upload/academic", files=files, data=data, headers={"HX-Request": "true"})
    assert response.status_code == 200
    assert "supera el tamaño máximo" in response.text

def test_upload_filename_sanitization():
    cookie = get_session_cookie("director")
    client.cookies.set(SESSION_COOKIE_NAME, cookie)

    csv_content = b"MATRICULA,ALUMNO,Grupo,Language Arts,Matem\xc3\xa1ticas,Espa\xc3\xb1ol,Nivel\n102,Maria Lopez,1A,9.0,9.5,9.2,Primaria\n"
    files = {"file": ("../../../../etc/passwd.csv", io.BytesIO(csv_content), "text/csv")}
    data = {"ciclo": "2025 - 2026", "campus": "Misiones"}

    response = client.post("/upload/academic", files=files, data=data, headers={"HX-Request": "true"})
    assert response.status_code == 200
    assert "passwd.csv" in response.text
    assert "../" not in response.text

def test_upload_rbac_isolation():
    client.cookies.clear()
    response = client.get("/upload")
    assert response.status_code == 307
    assert response.headers["location"] == "/login"
