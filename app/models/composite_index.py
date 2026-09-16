# app/models/composite_index.py

from typing import List, Dict, Literal
from pydantic import BaseModel, Field

class CompositePoint(BaseModel):
    campus: str = Field(..., description="Nombre del campus o 'Global'")
    bimestre: str = Field(..., description="Bimestre B1..B5")
    bimestre_label: str = Field(..., description="Etiqueta legible del bimestre, ej. 'B1 (Sep-Oct)'")
    indice: float = Field(..., description="Valor del índice compuesto (0 - 100)")
    tipo: Literal["Real", "Proyección"] = Field(..., description="Indica si es dato histórico real o proyección futura")

class CampusStatus(BaseModel):
    indice_actual: float = Field(..., description="Índice compuesto actual (B3)")
    indice_b5: float = Field(..., description="Proyección del índice compuesto a B5")
    global_b3: float = Field(..., description="Promedio global en B3")
    diff: float = Field(..., description="Diferencia contra el promedio global")
    estado: Literal["ok", "warning", "risk", "info"] = Field(..., description="Estado para el semáforo ejecutivo")
    color_hex: str = Field(..., description="Código de color hexadecimal")
    motivo: str = Field(..., description="Explicación del estado")

class CompositeIndexResponse(BaseModel):
    ciclo_escolar: str
    points: List[CompositePoint]
    status: Dict[str, CampusStatus]
