# app/routers/upload.py

import os
import pathlib
import io
import pandas as pd
from typing import Optional
from fastapi import APIRouter, Request, Form, UploadFile, File, Depends, HTTPException, status
from fastapi.responses import HTMLResponse
from fastapi.templating import Jinja2Templates

from app.config import settings
from app.models.user import UserBase
from app.routers.auth import get_current_user, require_role, get_current_user_optional, resolve_campus_for_user
from app.services.data_repository import DataRepository
from app.services.audit_service import registrar_evento_auditoria
from app.services.academic_service import parse_academic_excel, InvalidFileFormatException
from app.services.ixl_service import parse_ixl_diagnostic
from app.services.asistencia_service import parse_asistencia_file
from app.services.clima_disciplina_service import parse_clima_disciplina_file

router = APIRouter(prefix="/upload", tags=["Upload"])
templates = Jinja2Templates(directory="app/templates")

ALLOWED_EXCEL_EXTENSIONS = {".xlsx", ".xls"}
ALLOWED_CSV_EXTENSIONS = {".csv"}
ALLOWED_EXTENSIONS = ALLOWED_EXCEL_EXTENSIONS | ALLOWED_CSV_EXTENSIONS

ALLOWED_MIMETYPES = {
    "application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
    "application/vnd.ms-excel",
    "text/csv",
    "application/csv",
    "text/plain",
    "application/octet-stream"
}

def validate_and_sanitize_file(file: UploadFile, content: bytes) -> str:
    """
    Sanitiza el nombre de archivo (path traversal),
    comprueba el tamaño máximo permitido y verifica extensión + tipo MIME real.
    """
    raw_name = file.filename or "archivo.bin"
    clean_filename = pathlib.Path(raw_name).name
    clean_filename = "".join(c for c in clean_filename if c.isalnum() or c in (".", "_", "-")).strip()
    if not clean_filename:
        clean_filename = "archivo_procesado.bin"

    # 1. Validar Tamaño Máximo
    max_bytes = settings.MAX_UPLOAD_SIZE_MB * 1024 * 1024
    if len(content) > max_bytes:
        raise HTTPException(
            status_code=status.HTTP_413_CONTENT_TOO_LARGE,
            detail=f"El archivo supera el tamaño máximo permitido de {settings.MAX_UPLOAD_SIZE_MB}MB."
        )

    # 2. Validar Extensión
    ext = os.path.splitext(clean_filename)[1].lower()
    if ext not in ALLOWED_EXTENSIONS:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Extensión '{ext}' no permitida. Solo se aceptan archivos Excel (.xlsx, .xls) o CSV (.csv)."
        )

    # 3. Validar Tipo MIME (Verificación cruzada)
    content_type = (file.content_type or "").lower()
    if content_type and content_type not in ALLOWED_MIMETYPES:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Tipo MIME '{content_type}' no válido. El tipo de archivo no corresponde a un documento Excel o CSV auténtico."
        )

    # Inspección básica de Firma de Bytes (Magic bytes)
    if ext in ALLOWED_EXCEL_EXTENSIONS and ext == ".xlsx":
        if not content.startswith(b"PK\x03\x04"):
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Firma de archivo inválida. El archivo no es un documento Excel OpenXML auténtico."
            )

    return clean_filename

@router.get("", response_class=HTMLResponse)
async def render_upload_page(
    request: Request,
    user: UserBase = Depends(require_role(["General", "Misiones", "Nuevo Sur", "San Agustín"]))
):
    return templates.TemplateResponse(
        request=request,
        name="pages/upload.html",
        context={"user": user, "active_tab": "upload"}
    )

@router.post("/academic", response_class=HTMLResponse)
async def upload_academic_file(
    request: Request,
    file: UploadFile = File(...),
    ciclo: str = Form("2025 - 2026"),
    campus: str = Form("Global"),
    user: UserBase = Depends(require_role(["General", "Misiones", "Nuevo Sur", "San Agustín"]))
):
    repo = DataRepository()
    try:
        content = await file.read()
        sanitized_name = validate_and_sanitize_file(file, content)

        # Si el usuario es de un campus específico, forzar ese campus
        user_campus = resolve_campus_for_user(user, campus)

        df = parse_academic_excel(content, ciclo_escolar=ciclo, campus=user_campus)
        if df.empty:
            raise InvalidFileFormatException("El archivo no contiene registros válidos de calificaciones.")

        repo.save_dataframe_table(df, "academic_data", if_exists="append")

        registrar_evento_auditoria(
            usuario=user.username,
            accion="UPLOAD_ACADEMIC",
            detalle=f"Carga exitosa de {len(df)} calificaciones desde '{sanitized_name}' ({ciclo})",
            campus=user_campus,
            ciclo_escolar=ciclo,
            repo=repo
        )

        context = {
            "success": True,
            "message": f"Se procesaron e ingresaron exitosamente {len(df)} registros de calificaciones.",
            "filename": sanitized_name,
            "ciclo": ciclo,
            "campus": user_campus
        }
    except HTTPException as he:
        context = {"success": False, "error": he.detail}
    except InvalidFileFormatException as ie:
        context = {"success": False, "error": str(ie)}
    except Exception as e:
        context = {"success": False, "error": f"Error inesperado procesando archivo: {str(e)}"}

    if "hx-request" in request.headers:
        return templates.TemplateResponse(request=request, name="fragments/upload_status.html", context=context)
    return templates.TemplateResponse(request=request, name="pages/upload.html", context={"user": user, "active_tab": "upload", **context})

@router.post("/ixl", response_class=HTMLResponse)
async def upload_ixl_file(
    request: Request,
    file: UploadFile = File(...),
    ciclo: str = Form("2025 - 2026"),
    campus: str = Form("Global"),
    user: UserBase = Depends(require_role(["General", "Misiones", "Nuevo Sur", "San Agustín"]))
):
    repo = DataRepository()
    try:
        content = await file.read()
        sanitized_name = validate_and_sanitize_file(file, content)
        user_campus = resolve_campus_for_user(user, campus)

        df = parse_ixl_diagnostic(content, ciclo_escolar=ciclo, campus=user_campus)
        if df.empty:
            raise InvalidFileFormatException("El reporte IXL no contiene registros diagnósticos válidos.")

        repo.save_dataframe_table(df, "ixl_diagnostics", if_exists="append")

        registrar_evento_auditoria(
            usuario=user.username,
            accion="UPLOAD_IXL",
            detalle=f"Carga exitosa de {len(df)} registros IXL desde '{sanitized_name}' ({ciclo})",
            campus=user_campus,
            ciclo_escolar=ciclo,
            repo=repo
        )

        context = {
            "success": True,
            "message": f"Se ingresaron exitosamente {len(df)} diagnósticos de dominio IXL.",
            "filename": sanitized_name,
            "ciclo": ciclo,
            "campus": user_campus
        }
    except HTTPException as he:
        context = {"success": False, "error": he.detail}
    except InvalidFileFormatException as ie:
        context = {"success": False, "error": str(ie)}
    except Exception as e:
        context = {"success": False, "error": f"Error inesperado procesando reporte IXL: {str(e)}"}

    if "hx-request" in request.headers:
        return templates.TemplateResponse(request=request, name="fragments/upload_status.html", context=context)
    return templates.TemplateResponse(request=request, name="pages/upload.html", context={"user": user, "active_tab": "upload", **context})

@router.post("/asistencia", response_class=HTMLResponse)
async def upload_asistencia_file(
    request: Request,
    file: UploadFile = File(...),
    ciclo: str = Form("2025 - 2026"),
    campus: str = Form("Global"),
    user: UserBase = Depends(require_role(["General", "Misiones", "Nuevo Sur", "San Agustín"]))
):
    repo = DataRepository()
    try:
        content = await file.read()
        sanitized_name = validate_and_sanitize_file(file, content)
        user_campus = resolve_campus_for_user(user, campus)

        df = parse_asistencia_file(content, ciclo_escolar=ciclo, campus=user_campus)
        if df.empty:
            raise InvalidFileFormatException("El archivo no contiene datos de asistencia válidos.")

        repo.save_dataframe_table(df, "attendance_data", if_exists="append")

        registrar_evento_auditoria(
            usuario=user.username,
            accion="UPLOAD_ATTENDANCE",
            detalle=f"Carga exitosa de {len(df)} registros de asistencia desde '{sanitized_name}' ({ciclo})",
            campus=user_campus,
            ciclo_escolar=ciclo,
            repo=repo
        )

        context = {
            "success": True,
            "message": f"Se procesaron exitosamente {len(df)} registros de asistencia escolar.",
            "filename": sanitized_name,
            "ciclo": ciclo,
            "campus": user_campus
        }
    except HTTPException as he:
        context = {"success": False, "error": he.detail}
    except InvalidFileFormatException as ie:
        context = {"success": False, "error": str(ie)}
    except Exception as e:
        context = {"success": False, "error": f"Error inesperado procesando asistencia: {str(e)}"}

    if "hx-request" in request.headers:
        return templates.TemplateResponse(request=request, name="fragments/upload_status.html", context=context)
    return templates.TemplateResponse(request=request, name="pages/upload.html", context={"user": user, "active_tab": "upload", **context})

@router.post("/clima_disciplina", response_class=HTMLResponse)
async def upload_clima_disciplina_file(
    request: Request,
    file: UploadFile = File(...),
    tipo: str = Form("clima"),
    ciclo: str = Form("2025 - 2026"),
    campus: str = Form("Global"),
    user: UserBase = Depends(require_role(["General", "Misiones", "Nuevo Sur", "San Agustín"]))
):
    repo = DataRepository()
    try:
        content = await file.read()
        sanitized_name = validate_and_sanitize_file(file, content)
        user_campus = resolve_campus_for_user(user, campus)

        df = parse_clima_disciplina_file(content, tipo=tipo, ciclo_escolar=ciclo, campus=user_campus)
        if df.empty:
            raise InvalidFileFormatException(f"El archivo no contiene registros válidos para {tipo}.")

        table_name = "clima_data" if tipo == "clima" else "disciplina_casos"
        repo.save_dataframe_table(df, table_name, if_exists="append")

        registrar_evento_auditoria(
            usuario=user.username,
            accion=f"UPLOAD_{tipo.upper()}",
            detalle=f"Carga exitosa de {len(df)} registros de {tipo} desde '{sanitized_name}' ({ciclo})",
            campus=user_campus,
            ciclo_escolar=ciclo,
            repo=repo
        )

        context = {
            "success": True,
            "message": f"Se procesaron e ingresaron exitosamente {len(df)} registros de {tipo}.",
            "filename": sanitized_name,
            "ciclo": ciclo,
            "campus": user_campus
        }
    except HTTPException as he:
        context = {"success": False, "error": he.detail}
    except InvalidFileFormatException as ie:
        context = {"success": False, "error": str(ie)}
    except Exception as e:
        context = {"success": False, "error": f"Error inesperado procesando archivo de {tipo}: {str(e)}"}

    if "hx-request" in request.headers:
        return templates.TemplateResponse(request=request, name="fragments/upload_status.html", context=context)
    return templates.TemplateResponse(request=request, name="pages/upload.html", context={"user": user, "active_tab": "upload", **context})
