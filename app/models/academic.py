# app/models/academic.py

from typing import List, Optional, Dict
from pydantic import BaseModel, Field

class SubjectGrade(BaseModel):
    materia: str
    promedio: float
    previo: Optional[float] = None
    delta: Optional[float] = None

class LevelAcademicSummary(BaseModel):
    nivel: str
    total_alumnos: int
    pct_desempeno: float
    promedio_matematicas: float
    promedio_espanol: float
    promedio_language_arts: float

class AcademicBlockSummary(BaseModel):
    bloque: str
    campus: str
    ciclo_escolar: str
    total_alumnos: int
    promedio_matematicas: float
    promedio_espanol: float
    promedio_language_arts: float
    pct_en_desempeno: float
    niveles: List[LevelAcademicSummary] = []
