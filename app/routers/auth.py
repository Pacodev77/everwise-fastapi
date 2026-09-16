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
    """Firma los datos del usuario y genera una cookie HTTP-Only segura."""
    token = serializer.dumps(user_data)
    response.set_cookie(
        key=SESSION_COOKIE_NAME,
        value=token,
        max_age=MAX_AGE_SECONDS,
        httponly=True,
        samesite="lax",
        secure=False  # Cambiar a True en HTTPS producción
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
            is_active=True
        )
    except (BadSignature, SignatureExpired, KeyError):
        return None

def get_current_user(request: Request) -> UserBase:
    """Dependencia FastAPI que exige usuario autenticado."""
    user = get_current_user_optional(request)
    if not user:
        raise HTTPException(
            status_code=status.HTTP_307_TEMPORARY_REDIRECT,
            headers={"Location": "/login"}
        )
    return user

def require_role(allowed_roles: List[str]):
    """Dependencia de autorización basada en roles (RBAC)."""
    def role_checker(user: UserBase = Depends(get_current_user)):
        if user.role not in allowed_roles and "General" not in allowed_roles:
            if user.role in ["Misiones", "Nuevo Sur", "San Agustín"]:
                campus_slug = user.role.lower().replace(" ", "")
                raise HTTPException(
                    status_code=status.HTTP_307_TEMPORARY_REDIRECT,
                    headers={"Location": f"/campus/{campus_slug}"}
                )
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
        user_data = {
            "username": user_db.username,
            "role": user_db.role,
            "name": user_db.name,
            "email": user_db.email
        }
        
        # Determinar URL de redirección según rol (RBAC)
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
            detalle=f"Inicio de sesión exitoso con rol {user_db.role} (Bcrypt auth)",
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
