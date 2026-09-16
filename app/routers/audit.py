# app/routers/audit.py

import io
import csv
from typing import Optional
from fastapi import APIRouter, Request, Depends, Query, Response
from fastapi.responses import HTMLResponse
from fastapi.templating import Jinja2Templates

from app.models.user import UserBase
from app.routers.auth import require_role, get_current_user
from app.services.data_repository import DataRepository

router = APIRouter(prefix="/audit", tags=["Audit CRM"])
templates = Jinja2Templates(directory="app/templates")

@router.get("", response_class=HTMLResponse)
async def render_audit_page(
    request: Request,
    user: UserBase = Depends(require_role(["General", "Misiones", "Nuevo Sur", "San Agustín"]))
):
    return templates.TemplateResponse(
        request=request,
        name="pages/audit.html",
        context={"user": user, "active_tab": "audit"}
    )

@router.get("/fragments/table", response_class=HTMLResponse)
async def render_audit_table_fragment(
    request: Request,
    ciclo: Optional[str] = Query(None),
    search: Optional[str] = Query(None),
    user: UserBase = Depends(require_role(["General", "Misiones", "Nuevo Sur", "San Agustín"]))
):
    repo = DataRepository()
    raw_logs = repo.get_audit_logs(limit=150, ciclo_escolar=ciclo)

    # Filtrar por rol de campus si el usuario no es Director General
    if user.role != "General":
        raw_logs = [log for log in raw_logs if log.get("Campus") in [user.role, "Global"]]

    # Filtrar por búsqueda si se especificó
    if search:
        search_lower = search.strip().lower()
        raw_logs = [
            log for log in raw_logs
            if search_lower in str(log.get("Usuario", "")).lower()
            or search_lower in str(log.get("Acción", "")).lower()
            or search_lower in str(log.get("Detalle", "")).lower()
        ]

    return templates.TemplateResponse(
        request=request,
        name="fragments/audit_table.html",
        context={"user": user, "logs": raw_logs}
    )

@router.get("/export")
async def export_audit_csv(
    ciclo: Optional[str] = Query(None),
    user: UserBase = Depends(get_current_user)
):
    """
    Exportación de bitácora CRM en formato CSV.
    REQUERIMIENTO DE SEGURIDAD: Los datos se filtran estrictamente por el rol del usuario ANTES de ser generados.
    """
    repo = DataRepository()
    raw_logs = repo.get_audit_logs(limit=1000, ciclo_escolar=ciclo)

    # Filtrar en memoria / BD según rol de campus
    if user.role != "General":
        filtered_logs = [log for log in raw_logs if log.get("Campus") == user.role]
    else:
        filtered_logs = raw_logs

    output = io.StringIO()
    writer = csv.writer(output)
    writer.writerow(["ID", "Usuario", "Acción", "Detalle", "Campus", "Ciclo Escolar", "Timestamp"])

    for log in filtered_logs:
        writer.writerow([
            log.get("id", ""),
            log.get("Usuario", ""),
            log.get("Acción", ""),
            log.get("Detalle", ""),
            log.get("Campus", ""),
            log.get("Ciclo Escolar", log.get("ciclo_escolar", "")),
            log.get("Timestamp", "")
        ])

    csv_data = output.getvalue()
    filename = f"bitacora_auditoria_{user.role.lower().replace(' ', '_')}.csv"

    return Response(
        content=csv_data,
        media_type="text/csv",
        headers={"Content-Disposition": f'attachment; filename="{filename}"'}
    )
