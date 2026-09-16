# app/routers/clima_disciplina.py

from typing import Optional
from fastapi import APIRouter, Request, Depends, Query
from fastapi.responses import HTMLResponse
from fastapi.templating import Jinja2Templates

from app.models.user import UserBase
from app.routers.auth import require_role
from app.services.data_repository import DataRepository
from app.services.clima_disciplina_service import get_clima_summary, get_disciplina_summary

router = APIRouter(tags=["Clima & Disciplina"])
templates = Jinja2Templates(directory="app/templates")

@router.get("/clima", response_class=HTMLResponse)
async def render_clima_page(
    request: Request,
    user: UserBase = Depends(require_role(["General", "Misiones", "Nuevo Sur", "San Agustín"]))
):
    return templates.TemplateResponse(
        request=request,
        name="pages/clima.html",
        context={"user": user, "active_tab": "clima"}
    )

@router.get("/disciplina", response_class=HTMLResponse)
async def render_disciplina_page(
    request: Request,
    user: UserBase = Depends(require_role(["General", "Misiones", "Nuevo Sur", "San Agustín"]))
):
    return templates.TemplateResponse(
        request=request,
        name="pages/disciplina.html",
        context={"user": user, "active_tab": "disciplina"}
    )

@router.get("/clima/fragments/content", response_class=HTMLResponse)
async def render_clima_fragment(
    request: Request,
    ciclo: str = Query("2025 - 2026"),
    campus: Optional[str] = Query(None),
    user: UserBase = Depends(require_role(["General", "Misiones", "Nuevo Sur", "San Agustín"]))
):
    repo = DataRepository()
    user_campus = user.role if user.role != "General" else (campus or "Global")
    summary = get_clima_summary(ciclo_escolar=ciclo, campus=user_campus, repo=repo)

    return templates.TemplateResponse(
        request=request,
        name="fragments/clima_content.html",
        context={"user": user, "ciclo": ciclo, "campus": user_campus, "summary": summary}
    )

@router.get("/disciplina/fragments/content", response_class=HTMLResponse)
async def render_disciplina_fragment(
    request: Request,
    ciclo: str = Query("2025 - 2026"),
    campus: Optional[str] = Query(None),
    user: UserBase = Depends(require_role(["General", "Misiones", "Nuevo Sur", "San Agustín"]))
):
    repo = DataRepository()
    user_campus = user.role if user.role != "General" else (campus or "Global")
    summary = get_disciplina_summary(ciclo_escolar=ciclo, campus=user_campus, repo=repo)

    return templates.TemplateResponse(
        request=request,
        name="fragments/disciplina_content.html",
        context={"user": user, "ciclo": ciclo, "campus": user_campus, "summary": summary}
    )
