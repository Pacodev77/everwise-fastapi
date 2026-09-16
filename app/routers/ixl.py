# app/routers/ixl.py

from typing import Optional
from fastapi import APIRouter, Request, Depends, Query
from fastapi.responses import HTMLResponse
from fastapi.templating import Jinja2Templates

from app.models.user import UserBase
from app.routers.auth import require_role, resolve_campus_for_user
from app.services.data_repository import DataRepository
from app.services.ixl_service import get_ixl_summary

router = APIRouter(prefix="/ixl", tags=["IXL"])
templates = Jinja2Templates(directory="app/templates")

@router.get("", response_class=HTMLResponse)
async def render_ixl_page(
    request: Request,
    user: UserBase = Depends(require_role(["General", "Misiones", "Nuevo Sur", "San Agustín"]))
):
    return templates.TemplateResponse(
        request=request,
        name="pages/ixl.html",
        context={"user": user, "active_tab": "ixl"}
    )

@router.get("/fragments/content", response_class=HTMLResponse)
async def render_ixl_fragment(
    request: Request,
    ciclo: str = Query("2025 - 2026"),
    campus: Optional[str] = Query(None),
    user: UserBase = Depends(require_role(["General", "Misiones", "Nuevo Sur", "San Agustín"]))
):
    repo = DataRepository()
    user_campus = resolve_campus_for_user(user, campus)

    summary = get_ixl_summary(ciclo_escolar=ciclo, campus=user_campus, repo=repo)

    return templates.TemplateResponse(
        request=request,
        name="fragments/ixl_content.html",
        context={
            "user": user,
            "ciclo": ciclo,
            "campus": user_campus,
            "summary": summary
        }
    )
