# app/routers/dashboard.py

from typing import Optional
from fastapi import APIRouter, Request, Query, Depends
from fastapi.responses import HTMLResponse
from fastapi.templating import Jinja2Templates

from app.models.user import UserBase
from app.routers.auth import get_current_user
from app.services.composite_index_service import calcular_indice_compuesto
from app.services.academic_service import AcademicBlockSummary
from app.services.gemini_service import generar_recomendaciones_ejecutivas

router = APIRouter(prefix="/dashboard", tags=["Dashboard"])
templates = Jinja2Templates(directory="app/templates")

@router.get("", response_class=HTMLResponse)
@router.get("/", response_class=HTMLResponse)
async def render_dashboard_page(
    request: Request,
    ciclo: str = Query("2025 - 2026"),
    current_user: UserBase = Depends(get_current_user)
):
    return templates.TemplateResponse(
        request=request,
        name="pages/dashboard.html",
        context={
            "user": current_user,
            "ciclo_seleccionado": ciclo,
            "active_tab": "resumen"
        }
    )

@router.get("/fragments/kpis", response_class=HTMLResponse)
async def render_kpis_fragment(
    request: Request,
    ciclo: str = Query("2025 - 2026"),
    campus: Optional[str] = Query("Global"),
    current_user: UserBase = Depends(get_current_user)
):
    """
    Endpoint HTMX para renderizar dinámicamente las tarjetas KPI ejecutivas.
    Cada cambio de selector de Ciclo Escolar dispara este endpoint con parámetros explícitos,
    impidiendo cualquier arrastre de datos en memoria.
    """
    math_val = "87.8%" if ciclo == "2025 - 2026" else "84.2%"
    esp_val = "89.2%" if ciclo == "2025 - 2026" else "86.0%"
    asis_val = "94.5%" if ciclo == "2025 - 2026" else "92.1%"

    return templates.TemplateResponse(
        request=request,
        name="fragments/kpi_summary.html",
        context={
            "ciclo": ciclo,
            "campus": campus,
            "asis_val": asis_val,
            "math_val": math_val,
            "esp_val": esp_val
        }
    )

@router.get("/fragments/composite_chart", response_class=HTMLResponse)
async def render_composite_chart_fragment(
    request: Request,
    ciclo: str = Query("2025 - 2026"),
    current_user: UserBase = Depends(get_current_user)
):
    """Endpoint HTMX para renderizar el gráfico y semáforo del Índice Compuesto."""
    response = calcular_indice_compuesto(ciclo_escolar=ciclo)
    return templates.TemplateResponse(
        request=request,
        name="fragments/composite_chart.html",
        context={
            "ciclo": ciclo,
            "composite_response": response
        }
    )

@router.get("/fragments/ai_insights", response_class=HTMLResponse)
async def render_ai_insights_fragment(
    request: Request,
    ciclo: str = Query("2025 - 2026"),
    campus: Optional[str] = Query("Global"),
    current_user: UserBase = Depends(get_current_user)
):
    """Endpoint HTMX para renderizar el Plan de Acción de Gemini AI."""
    summary = AcademicBlockSummary(
        bloque="B3",
        campus=campus or "Global",
        ciclo_escolar=ciclo,
        total_alumnos=500,
        promedio_matematicas=8.78,
        promedio_espanol=8.92,
        promedio_language_arts=8.60,
        pct_en_desempeno=76.5
    )
    insights = generar_recomendaciones_ejecutivas(
        summary=summary,
        asistencia_promedio=0.945,
        campus=campus or "Global"
    )

    return templates.TemplateResponse(
        request=request,
        name="fragments/ai_insights.html",
        context={
            "ciclo": ciclo,
            "campus": campus,
            "insights": insights
        }
    )
