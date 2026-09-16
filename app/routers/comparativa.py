# app/routers/comparativa.py

from typing import Optional, Dict, Any
from fastapi import APIRouter, Request, Depends, Query
from fastapi.responses import HTMLResponse
from fastapi.templating import Jinja2Templates

from app.models.user import UserBase
from app.routers.auth import require_role
from app.services.composite_index_service import calcular_indice_compuesto

router = APIRouter(prefix="/comparativa", tags=["Comparativa Multicampus"])
templates = Jinja2Templates(directory="app/templates")

def calcular_semaforo_desviacion(desviacion_pct: float) -> str:
    """
    Calcula el nivel de semáforo según la desviación en puntos porcentuales (0-100) respecto a la media global:
    - 🟢 Verde: Desviación >= -3.0% (En u Óptimo sobre la norma)
    - 🟡 Amarillo: Desviación entre -3.0% y -5.0% (Alerta Moderada)
    - 🔴 Rojo: Desviación < -5.0% (Alerta Crítica)
    """
    if desviacion_pct >= -3.0:
        return "verde"
    elif desviacion_pct >= -5.0:
        return "amarillo"
    else:
        return "rojo"

@router.get("", response_class=HTMLResponse)
async def render_comparativa_page(
    request: Request,
    user: UserBase = Depends(require_role(["General"]))
):
    return templates.TemplateResponse(
        request=request,
        name="pages/comparativa.html",
        context={"user": user, "active_tab": "comparativa"}
    )

@router.get("/fragments/content", response_class=HTMLResponse)
async def render_comparativa_fragment(
    request: Request,
    ciclo: str = Query("2025 - 2026"),
    user: UserBase = Depends(require_role(["General"]))
):
    composite_resp = calcular_indice_compuesto(ciclo_escolar=ciclo)
    promedio_global = composite_resp.status["Global"].indice_actual

    campus_data_b3 = {
        "Misiones": {"matricula": 180, "acad": 8.78, "ixl": 79.0, "asistencia": 84.0},
        "Nuevo Sur": {"matricula": 150, "acad": 9.05, "ixl": 86.0, "asistencia": 88.0},
        "San Agustín": {"matricula": 170, "acad": 8.08, "ixl": 71.0, "asistencia": 75.0},
    }

    comparativa_campus = []
    for campus in ["Misiones", "Nuevo Sur", "San Agustín"]:
        st = composite_resp.status[campus]
        idx_compuesto = st.indice_actual
        desviacion = round(idx_compuesto - promedio_global, 1)
        semaforo = calcular_semaforo_desviacion(desviacion)
        c_info = campus_data_b3[campus]

        comparativa_campus.append({
            "campus": campus,
            "matricula": c_info["matricula"],
            "promedio_academico": c_info["acad"],
            "pct_ixl": c_info["ixl"],
            "pct_asistencia": c_info["asistencia"],
            "indice_compuesto": idx_compuesto,
            "desviacion_pct": desviacion,
            "semaforo": semaforo
        })

    status_inst = "Satisfactorio"
    if all(item["semaforo"] == "verde" for item in comparativa_campus):
        status_inst = "Óptimo"
    elif any(item["semaforo"] == "rojo" for item in comparativa_campus):
        status_inst = "Atención Requerida"

    return templates.TemplateResponse(
        request=request,
        name="fragments/comparativa_content.html",
        context={
            "user": user,
            "ciclo": ciclo,
            "promedio_global": promedio_global,
            "status_institucional": status_inst,
            "comparativa_campus": comparativa_campus
        }
    )
