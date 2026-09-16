# app/models/audit.py

from typing import Optional
from datetime import datetime
from pydantic import BaseModel, Field

class AuditLogEntry(BaseModel):
    id: Optional[int] = None
    usuario: str
    accion: str
    detalle: str
    campus: Optional[str] = "Global"
    ciclo_escolar: Optional[str] = "2025 - 2026"
    timestamp: str = Field(default_factory=lambda: datetime.now().strftime("%Y-%m-%d %H:%M:%S"))
