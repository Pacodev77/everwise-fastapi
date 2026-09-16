# app/routers/auth.py

from typing import Optional, List
from fastapi import APIRouter, Request, Form, Depends, HTTPException, status, Response
from fastapi.responses import HTMLResponse, RedirectResponse
from fastapi.templating import Jinja2Templates
from itsdangerous import URLSafeTimedSerializer, BadSignature, SignatureExpired

from app.config import settings
from app.models.user import UserBase
from app.services.data_repository import DataRepository
from app.services.audit_service import registrar_evento_auditoria

router = APIRouter(tags=["Authentication"])
templates = Jinja2Templates(directory="app/templates")
serializer = URLSafeTimedSerializer(settings.SECRET_AUTH_KEY)

SESSION_COOKIE_NAME = "everwise_session"
MAX_AGE_SECONDS = 86400  # 24 Horas

def create_session_cookie(response: Response, user_data: dict):
    """Firma los datos del usuario y genera una cookie de sesión HTTP-Only, SameSite=Lax y Secure."""
    token = serializer.dumps(user_data)
    response.set_cookie(
        key=SESSION_COOKIE_NAME,
        value=token,
        max_age=MAX_AGE_SECONDS,
        httponly=True,
        samesite="lax",
        secure=settings.COOKIE_SECURE
    )

def get_current_user_optional(request: Request) -> Optional[UserBase]:
    """Obtiene el usuario actual de la cookie firmada sin lanzar excepción."""
    token = request.cookies.get(SESSION_COOKIE_NAME)
    if not token:
        return None
    try:
        data = serializer.loads(token, max_age=MAX_AGE_SECONDS)
        return UserBase(
            username=data["username"],
            role=data["role"],
            name=data["name"],
            email=data.get("email"),
            is_active=True,
            must_change_password=data.get("must_change_password", False)
        )
    except (BadSignature, SignatureExpired, KeyError):
        return None

def get_current_user(request: Request) -> UserBase:
    """Dependencia FastAPI que exige usuario autenticado y sin cambio de contraseña pendiente."""
    user = get_current_user_optional(request)
    if not user:
        raise HTTPException(
            status_code=status.HTTP_307_TEMPORARY_REDIRECT,
            headers={"Location": "/login"}
        )
    if user.must_change_password and request.url.path not in ["/change-password", "/logout"]:
        raise HTTPException(
            status_code=status.HTTP_307_TEMPORARY_REDIRECT,
            headers={"Location": "/change-password"}
        )
    return user

def require_role(allowed_roles: List[str]):
    """Dependencia de autorización basada en roles (RBAC). Retorna 403 Forbidden si el rol no está autorizado."""
    def role_checker(user: UserBase = Depends(get_current_user)):
        if user.role not in allowed_roles and "General" not in allowed_roles:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail=f"Acceso Restringido: Tu rol de '{user.role}' no cuenta con permisos para este recurso."
            )
        return user
    return role_checker

@router.get("/login", response_class=HTMLResponse)
async def render_login_page(request: Request):
    user = get_current_user_optional(request)
    if user:
        if user.must_change_password:
            return RedirectResponse(url="/change-password", status_code=status.HTTP_303_SEE_OTHER)
        return RedirectResponse(url="/dashboard", status_code=status.HTTP_303_SEE_OTHER)
    return templates.TemplateResponse(request=request, name="login.html", context={"error": None})

@router.post("/login", response_class=HTMLResponse)
async def login_post(
    request: Request,
    username: str = Form(...),
    password: str = Form(...)
):
    username_clean = username.strip().lower()
    repo = DataRepository()
    user_db = repo.get_user(username_clean)

    if not user_db:
        return templates.TemplateResponse(
            request=request,
            name="login.html", 
            context={"error": "Credenciales incorrectas o usuario inactivo."},
            status_code=status.HTTP_401_UNAUTHORIZED
        )

    # Verificar contraseña y realizar migración transparente a Bcrypt si era legacy SHA256 o '123'
    if repo.verify_password_and_migrate(username_clean, password, user_db.password_hash):
        # Volver a cargar el objeto actualizado
        user_updated = repo.get_user(username_clean)
        must_change = user_updated.must_change_password if user_updated else user_db.must_change_password

        user_data = {
            "username": user_db.username,
            "role": user_db.role,
            "name": user_db.name,
            "email": user_db.email,
            "must_change_password": must_change
        }
        
        # Redirigir a /change-password si must_change_password es True
        if must_change:
            redirect_url = "/change-password"
        else:
            redirect_url = "/dashboard"
            if user_db.role in ["Misiones", "Nuevo Sur", "San Agustín"]:
                campus_slug = user_db.role.lower().replace(" ", "")
                redirect_url = f"/campus/{campus_slug}"

        response = RedirectResponse(url=redirect_url, status_code=status.HTTP_303_SEE_OTHER)
        create_session_cookie(response, user_data)
        
        # Registrar evento en bitácora CRM
        registrar_evento_auditoria(
            usuario=user_db.username,
            accion="LOGIN",
            detalle=f"Inicio de sesión exitoso (Bcrypt auth, must_change={must_change})",
            campus=user_db.role if user_db.role != "General" else "Global",
            repo=repo
        )
        return response

    return templates.TemplateResponse(
        request=request,
        name="login.html", 
        context={"error": "Credenciales incorrectas o usuario inactivo."},
        status_code=status.HTTP_401_UNAUTHORIZED
    )

@router.get("/change-password", response_class=HTMLResponse)
async def render_change_password_page(request: Request):
    user = get_current_user_optional(request)
    if not user:
        return RedirectResponse(url="/login", status_code=status.HTTP_303_SEE_OTHER)
    if not user.must_change_password:
        return RedirectResponse(url="/dashboard", status_code=status.HTTP_303_SEE_OTHER)

    return templates.TemplateResponse(request=request, name="change_password.html", context={"error": None})

@router.post("/change-password", response_class=HTMLResponse)
async def change_password_post(
    request: Request,
    new_password: str = Form(...),
    confirm_password: str = Form(...)
):
    user = get_current_user_optional(request)
    if not user:
        return RedirectResponse(url="/login", status_code=status.HTTP_303_SEE_OTHER)

    if new_password != confirm_password:
        return templates.TemplateResponse(
            request=request,
            name="change_password.html",
            context={"error": "Las contraseñas no coinciden. Inténtalo de nuevo."}
        )

    if len(new_password) < 6:
        return templates.TemplateResponse(
            request=request,
            name="change_password.html",
            context={"error": "La contraseña debe tener al menos 6 caracteres."}
        )

    if new_password == "123":
        return templates.TemplateResponse(
            request=request,
            name="change_password.html",
            context={"error": "Debes elegir una contraseña diferente a la predeterminada '123'."}
        )

    repo = DataRepository()
    new_bcrypt_hash = repo.hash_password_bcrypt(new_password)
    repo.clear_must_change_password(user.username, new_bcrypt_hash)

    registrar_evento_auditoria(
        usuario=user.username,
        accion="CHANGE_PASSWORD",
        detalle="Actualización obligatoria de contraseña completada a Bcrypt",
        campus=user.role if user.role != "General" else "Global",
        repo=repo
    )

    # Actualizar la cookie declarando must_change_password = False
    user_data = {
        "username": user.username,
        "role": user.role,
        "name": user.name,
        "email": user.email,
        "must_change_password": False
    }

    redirect_url = "/dashboard"
    if user.role in ["Misiones", "Nuevo Sur", "San Agustín"]:
        campus_slug = user.role.lower().replace(" ", "")
        redirect_url = f"/campus/{campus_slug}"

    response = RedirectResponse(url=redirect_url, status_code=status.HTTP_303_SEE_OTHER)
    create_session_cookie(response, user_data)
    return response

@router.get("/logout")
@router.post("/logout")
async def logout(request: Request):
    user = get_current_user_optional(request)
    if user:
        registrar_evento_auditoria(
            usuario=user.username,
            accion="LOGOUT",
            detalle="Cierre de sesión de usuario",
            campus=user.role if user.role != "General" else "Global"
        )

    response = RedirectResponse(url="/login", status_code=status.HTTP_303_SEE_OTHER)
    response.delete_cookie(SESSION_COOKIE_NAME)
    return response
