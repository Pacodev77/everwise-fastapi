# app/services/audit_service.py

from typing import List, Dict, Any, Optional
from app.models.audit import AuditLogEntry
from app.services.data_repository import DataRepository

def registrar_evento_auditoria(
    usuario: str, 
    accion: str, 
    detalle: str, 
    campus: str = "Global", 
    ciclo_escolar: str = "2025 - 2026",
    repo: Optional[DataRepository] = None
):
    """Registra una acción o evento inmutable en la bitácora CRM."""
    repository = repo or DataRepository()
    entry = AuditLogEntry(
        usuario=usuario,
        accion=accion,
        detalle=detalle,
        campus=campus,
        ciclo_escolar=ciclo_escolar
    )
    repository.add_audit_log(entry)

def obtener_bitacora_auditoria(
    limit: int = 100, 
    ciclo_escolar: Optional[str] = None,
    repo: Optional[DataRepository] = None
) -> List[Dict[str, Any]]:
    """Consulta los registros recientes de la bitácora de auditoría CRM."""
    repository = repo or DataRepository()
    return repository.get_audit_logs(limit=limit, ciclo_escolar=ciclo_escolar)
