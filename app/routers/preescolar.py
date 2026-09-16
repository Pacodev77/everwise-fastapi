# app/routers/preescolar.py

from typing import Optional
from fastapi import APIRouter, Request, Depends, Query
from fastapi.responses import HTMLResponse
from fastapi.templating import Jinja2Templates

from app.models.user import UserBase
from app.routers.auth import require_role, resolve_campus_for_user

router = APIRouter(prefix="/preescolar", tags=["Preescolar Cualitativo"])
templates = Jinja2Templates(directory="app/templates")

RUBRICA_ESCALA_CUALITATIVA = [
    {"codigo": "D", "nombre": "Dominado / Sobresaliente", "badge": "badge-success", "descripcion": "Demuestra la habilidad de manera autónoma y fluida."},
    {"codigo": "L", "nombre": "Logrado / Satisfactorio", "badge": "badge-info", "descripcion": "Alcanza el aprendizaje esperado con guía regular."},
    {"codigo": "EP", "nombre": "En Proceso / En Desarrollo", "badge": "badge-warning", "descripcion": "Muestra avance pero requiere mediación constante."},
    {"codigo": "RA", "nombre": "Requiere Apoyo / Inicio", "badge": "badge-danger", "descripcion": "Presenta dificultades persistentes que exigen atención tutorial."}
]

@router.get("", response_class=HTMLResponse)
async def render_preescolar_page(
    request: Request,
    user: UserBase = Depends(require_role(["General", "Misiones", "Nuevo Sur", "San Agustín"]))
):
    return templates.TemplateResponse(
        request=request,
        name="pages/preescolar.html",
        context={"user": user, "active_tab": "preescolar"}
    )

@router.get("/fragments/content", response_class=HTMLResponse)
async def render_preescolar_fragment(
    request: Request,
    ciclo: str = Query("2025 - 2026"),
    campus: Optional[str] = Query(None),
    grado: str = Query("Todos"),
    user: UserBase = Depends(require_role(["General", "Misiones", "Nuevo Sur", "San Agustín"]))
):
    user_campus = resolve_campus_for_user(user, campus)

    # Evaluación puramente cualitativa (independiente del Índice Compuesto numérico)
    evaluaciones_cualitativas = [
        {
            "area": "Desarrollo Socioemocional & Autonomía",
            "indicador": "Autorregulación de emociones y convivencia armónica",
            "k1": "L (Logrado)",
            "k2": "D (Dominado)",
            "k3": "D (Dominado)",
            "estatus": "Optimo"
        },
        {
            "area": "Lenguaje & Comunicación",
            "indicador": "Oralidad, expresión de ideas y principios de lectoescritura",
            "k1": "EP (En Proceso)",
            "k2": "L (Logrado)",
            "k3": "L (Logrado)",
            "estatus": "En Norma"
        },
        {
            "area": "Pensamiento Matemático",
            "indicador": "Conteo, noción de cantidad y correspondencia uno a uno",
            "k1": "L (Logrado)",
            "k2": "L (Logrado)",
            "k3": "D (Dominado)",
            "estatus": "Optimo"
        },
        {
            "area": "Exploración del Mundo Natural & Social",
            "indicador": "Curiosidad por su entorno, hábitos de higiene y cuidado personal",
            "k1": "D (Dominado)",
            "k2": "D (Dominado)",
            "k3": "D (Dominado)",
            "estatus": "Sobresaliente"
        }
    ]

    return templates.TemplateResponse(
        request=request,
        name="fragments/preescolar_content.html",
        context={
            "user": user,
            "ciclo": ciclo,
            "campus": user_campus,
            "grado": grado,
            "escala": RUBRICA_ESCALA_CUALITATIVA,
            "evaluaciones": evaluaciones_cualitativas
        }
    )
