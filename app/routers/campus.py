# app/routers/campus.py

from fastapi import APIRouter, Request, Depends
from fastapi.responses import HTMLResponse
from fastapi.templating import Jinja2Templates

from app.models.user import UserBase
from app.routers.auth import require_role

router = APIRouter(prefix="/campus", tags=["Campus"])
templates = Jinja2Templates(directory="app/templates")

@router.get("/misiones", response_class=HTMLResponse)
async def render_misiones_campus_page(
    request: Request,
    user: UserBase = Depends(require_role(["General", "Misiones"]))
):
    return templates.TemplateResponse(
        request=request,
        name="pages/dashboard.html",
        context={"user": user, "active_tab": "misiones", "ciclo_seleccionado": "2025 - 2026"}
    )

@router.get("/nuevosur", response_class=HTMLResponse)
async def render_nuevosur_campus_page(
    request: Request,
    user: UserBase = Depends(require_role(["General", "Nuevo Sur"]))
):
    return templates.TemplateResponse(
        request=request,
        name="pages/dashboard.html",
        context={"user": user, "active_tab": "nuevosur", "ciclo_seleccionado": "2025 - 2026"}
    )

@router.get("/sanagustin", response_class=HTMLResponse)
async def render_sanagustin_campus_page(
    request: Request,
    user: UserBase = Depends(require_role(["General", "San Agustín"]))
):
    return templates.TemplateResponse(
        request=request,
        name="pages/dashboard.html",
        context={"user": user, "active_tab": "sanagustin", "ciclo_seleccionado": "2025 - 2026"}
    )
