# app/routers/academic.py

from typing import Optional
from fastapi import APIRouter, Request, Depends, Query
from fastapi.responses import HTMLResponse
from fastapi.templating import Jinja2Templates

from app.models.user import UserBase
from app.routers.auth import require_role
from app.services.data_repository import DataRepository
from app.services.academic_service import get_academic_summary

router = APIRouter(prefix="/academic", tags=["Academic"])
templates = Jinja2Templates(directory="app/templates")

@router.get("", response_class=HTMLResponse)
async def render_academic_page(
    request: Request,
    user: UserBase = Depends(require_role(["General", "Misiones", "Nuevo Sur", "San Agustín"]))
):
    return templates.TemplateResponse(
        request=request,
        name="pages/academic.html",
        context={"user": user, "active_tab": "academic"}
    )

@router.get("/fragments/content", response_class=HTMLResponse)
async def render_academic_fragment(
    request: Request,
    ciclo: str = Query("2025 - 2026"),
    campus: Optional[str] = Query(None),
    materia: str = Query("Todas"),
    user: UserBase = Depends(require_role(["General", "Misiones", "Nuevo Sur", "San Agustín"]))
):
    repo = DataRepository()
    user_campus = user.role if user.role != "General" else (campus or "Global")

    summary = get_academic_summary(ciclo_escolar=ciclo, campus=user_campus, repo=repo)

    return templates.TemplateResponse(
        request=request,
        name="fragments/academic_content.html",
        context={
            "user": user,
            "ciclo": ciclo,
            "campus": user_campus,
            "materia": materia,
            "summary": summary
        }
    )
