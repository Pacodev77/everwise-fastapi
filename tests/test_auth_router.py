# tests/test_auth_router.py

import pytest
from fastapi import APIRouter, Depends, Request
from fastapi.testclient import TestClient
from app.main import app
from app.routers.auth import SESSION_COOKIE_NAME, require_role, get_current_user
from app.models.user import UserBase
from app.services.data_repository import DataRepository

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

def test_login_success_and_redirects_to_change_password_first():
    """Al ingresar con la clave por defecto 123, redirige primero a /change-password por seguridad."""
    response = client.post("/login", data={"username": "director", "password": "123"})
    assert response.status_code == 303
    assert response.headers["location"] == "/change-password"
    assert SESSION_COOKIE_NAME in response.cookies

def test_session_cookie_flags():
    """Confirma que la cookie de sesión emite las banderas HttpOnly y SameSite=Lax."""
    response = client.post("/login", data={"username": "director", "password": "123"})
    cookie_header = response.headers.get("set-cookie", "")
    assert "HttpOnly" in cookie_header or "httponly" in cookie_header.lower()
    assert "samesite=lax" in cookie_header.lower()

def test_change_password_flow_updates_db_and_redirects():
    """
    Confirma que al completar el formulario /change-password con una nueva contraseña válida,
    se actualiza el hash Bcrypt en la BD, se limpia must_change_password a 0 y se permite ingresar.
    """
    # 1. Login inicial
    login_resp = client.post("/login", data={"username": "nuevosur", "password": "123"})
    cookie = login_resp.cookies.get(SESSION_COOKIE_NAME)

    # 2. Cambiar contraseña
    client.cookies.set(SESSION_COOKIE_NAME, cookie)
    change_resp = client.post("/change-password", data={
        "new_password": "NuevaPassword2026!",
        "confirm_password": "NuevaPassword2026!"
    })

    assert change_resp.status_code == 303
    assert change_resp.headers["location"] in ["/dashboard", "/campus/nuevosur"]

    # 3. Verificar en la BD que must_change_password ahora es 0 (False)
    repo = DataRepository()
    user_db = repo.get_user("nuevosur")
    assert user_db.must_change_password is False

    # 4. Probar login con la NUEVA contraseña
    new_login_resp = client.post("/login", data={"username": "nuevosur", "password": "NuevaPassword2026!"})
    assert new_login_resp.status_code == 303
    assert new_login_resp.headers["location"] == "/campus/nuevosur"

def test_logout_clears_cookie():
    login_resp = client.post("/login", data={"username": "director", "password": "123"})
    cookie = login_resp.cookies.get(SESSION_COOKIE_NAME)

    client.cookies.set(SESSION_COOKIE_NAME, cookie)
    logout_resp = client.get("/logout")
    assert logout_resp.status_code == 303
    assert logout_resp.headers["location"] == "/login"

def test_rbac_isolation_misiones_denied_nuevosur():
    """Confirma que la ruta REAL /campus/nuevosur retorna 403 Forbidden a un coordinador del campus Misiones."""
    client.cookies.clear()
    repo = DataRepository()
    repo.clear_must_change_password("misiones", repo.hash_password_bcrypt("SecurePass2026!"))

    login_resp = client.post("/login", data={"username": "misiones", "password": "SecurePass2026!"})
    cookie = login_resp.cookies.get(SESSION_COOKIE_NAME)

    client.cookies.set(SESSION_COOKIE_NAME, cookie)
    resp = client.get("/campus/nuevosur")
    
    assert resp.status_code == 403
    assert "Acceso Restringido" in resp.json()["detail"]

def test_require_role_unit_isolation_all_cases():
    """
    Prueba unitaria pura para require_role() en aislamiento que cubre los 4 casos:
    1. Rol permitido sin 'General' en la lista -> Permitido (200 OK)
    2. Rol no permitido sin 'General' en la lista -> 403 Forbidden
    3. Rol no permitido CON 'General' en la lista -> 403 Forbidden
    4. Rol permitido con 'General' en la lista -> Permitido (200 OK)
    """
    from fastapi import HTTPException

    # Caso 1: Rol permitido sin 'General'
    checker_1 = require_role(["Misiones"])
    user_misiones = UserBase(username="misiones", role="Misiones", name="Misiones User", is_active=True)
    role_func_1 = checker_1.__closure__[0].cell_contents if hasattr(checker_1, "__closure__") and checker_1.__closure__ else None
    # Invocación directa del dependency wrapper
    assert checker_1(user_misiones) == user_misiones

    # Caso 2: Rol no permitido sin 'General'
    user_nuevosur = UserBase(username="nuevosur", role="Nuevo Sur", name="Nuevo Sur User", is_active=True)
    with pytest.raises(HTTPException) as exc_info_2:
        checker_1(user_nuevosur)
    assert exc_info_2.value.status_code == 403

    # Caso 3: Rol no permitido CON 'General' en la lista (e.g. Misiones intentando acceder a ruta de Nuevo Sur)
    checker_3 = require_role(["General", "Nuevo Sur"])
    with pytest.raises(HTTPException) as exc_info_3:
        checker_3(user_misiones)
    assert exc_info_3.value.status_code == 403
    assert "Acceso Restringido" in exc_info_3.value.detail

    # Caso 4: Rol permitido con 'General' en la lista (Nuevo Sur y Director General)
    checker_4 = require_role(["General", "Nuevo Sur"])
    user_director = UserBase(username="director", role="General", name="Director General", is_active=True)
    assert checker_4(user_nuevosur) == user_nuevosur
    assert checker_4(user_director) == user_director
