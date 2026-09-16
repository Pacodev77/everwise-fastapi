# app/models/filter.py

from typing import Optional
from pydantic import BaseModel, Field

class FilterParams(BaseModel):
    ciclo_escolar: str = Field(default="2025 - 2026", description="Ciclo escolar activo, ej: '2025 - 2026'")
    campus: Optional[str] = Field(default=None, description="Campus seleccionado: 'Misiones', 'Nuevo Sur', 'San Agustín' o None/Global")
    bimestre: Optional[str] = Field(default="B3", description="Bimestre académico, ej: 'B1', 'B2', 'B3'")
