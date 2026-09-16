# app/models/ixl.py

from typing import List, Optional
from pydantic import BaseModel, Field

class IXLSubjectBand(BaseModel):
    rango: str
    alumnos_count: int
    porcentaje: float

class IXLSummary(BaseModel):
    campus: str
    ciclo_escolar: str
    total_estudiantes: int
    puntaje_promedio: float
    nivel_general: str
    distribucion_rangos: List[IXLSubjectBand] = []
