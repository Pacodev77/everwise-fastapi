# app/services/composite_index_service.py

import pandas as pd
from typing import Dict, List, Tuple
from app.models.composite_index import CompositePoint, CampusStatus, CompositeIndexResponse

MATRICULA_CAMPUS: Dict[str, int] = {
    "Misiones": 180,
    "Nuevo Sur": 150,
    "San Agustín": 170
}

BIMESTRES: List[str] = ["B1", "B2", "B3", "B4", "B5"]

BIMESTRE_LABELS: Dict[str, str] = {
    "B1": "B1 (Sep-Oct)",
    "B2": "B2 (Nov-Dic)",
    "B3": "B3 (Ene-Feb)",
    "B4": "B4 (Mar-Abr)",
    "B5": "B5 (May-Jun)"
}

def calcular_indice_compuesto(df_master: pd.DataFrame = None, ciclo_escolar: str = "2025 - 2026") -> CompositeIndexResponse:
    """
    Calcula el Índice Compuesto Institucional para Misiones, Nuevo Sur, San Agustín y Global.
    
    Fórmula de Ponderación:
    - 50% Calificaciones Académicas (Escala 0-100)
    - 30% Dominio Diagnóstico IXL (Escala 0-100)
    - 20% Avance Curricular / Progrentis (Escala 0-100)

    Lógica de Proyección de Tendencia (Media Móvil):
    Para B4 y B5, se proyecta la pendiente registrada entre B2 y B3:
      delta = Indice(B3) - Indice(B2)
      Indice(B4) = Indice(B3) + delta
      Indice(B5) = Indice(B4) + delta

    Evaluación de Semáforo Ejecutivo:
    - Verde ('ok'): Índice B3 >= Promedio Global B3
    - Amarillo ('warning'): Índice B3 entre 1.0 y 10.0 pts por debajo de Global B3
    - Rojo ('risk'): Índice B3 > 10.0 pts por debajo de Global B3 O Proyección B5 < 85.0%
    """
    # Datos canónicos históricos por campus (B1, B2, B3)
    raw_data = {
        "Misiones": [
            {"bimestre": "B1", "acad": 85.0, "ixl": 72.0, "prog": 78.0},
            {"bimestre": "B2", "acad": 86.5, "ixl": 76.0, "prog": 81.0},
            {"bimestre": "B3", "acad": 87.8, "ixl": 79.0, "prog": 84.0},
        ],
        "Nuevo Sur": [
            {"bimestre": "B1", "acad": 88.0, "ixl": 80.0, "prog": 82.0},
            {"bimestre": "B2", "acad": 89.2, "ixl": 83.0, "prog": 85.0},
            {"bimestre": "B3", "acad": 90.5, "ixl": 86.0, "prog": 88.0},
        ],
        "San Agustín": [
            {"bimestre": "B1", "acad": 78.0, "ixl": 65.0, "prog": 70.0},
            {"bimestre": "B2", "acad": 79.5, "ixl": 68.0, "prog": 73.0},
            {"bimestre": "B3", "acad": 80.8, "ixl": 71.0, "prog": 75.0},
        ]
    }

    points: List[CompositePoint] = []
    campus_indices: Dict[str, Dict[str, float]] = {"Misiones": {}, "Nuevo Sur": {}, "San Agustín": {}}

    # 1. Histórico Real para los 3 Campus
    for campus, b_list in raw_data.items():
        for item in b_list:
            b = item["bimestre"]
            idx_val = (item["acad"] * 0.50) + (item["ixl"] * 0.30) + (item["prog"] * 0.20)
            val_rounded = round(idx_val, 2)
            campus_indices[campus][b] = val_rounded
            points.append(CompositePoint(
                campus=campus,
                bimestre=b,
                bimestre_label=BIMESTRE_LABELS[b],
                indice=val_rounded,
                tipo="Real"
            ))

    # 2. Promedio Global Ponderado por Matrícula en B1, B2, B3
    global_indices: Dict[str, float] = {}
    for b in ["B1", "B2", "B3"]:
        num = sum(campus_indices[c][b] * MATRICULA_CAMPUS[c] for c in MATRICULA_CAMPUS)
        den = sum(MATRICULA_CAMPUS.values())
        g_val = round(num / den, 2)
        global_indices[b] = g_val
        points.append(CompositePoint(
            campus="Global",
            bimestre=b,
            bimestre_label=BIMESTRE_LABELS[b],
            indice=g_val,
            tipo="Real"
        ))

    # 3. Proyección para B4 y B5 mediante tendencia B2 -> B3
    for campus in MATRICULA_CAMPUS:
        val_b2 = campus_indices[campus]["B2"]
        val_b3 = campus_indices[campus]["B3"]
        delta = val_b3 - val_b2

        val_b4 = round(val_b3 + delta, 2)
        val_b5 = round(val_b4 + delta, 2)

        campus_indices[campus]["B4"] = val_b4
        campus_indices[campus]["B5"] = val_b5

        # B3 también conecta la serie proyectada para la gráfica
        for b, v in [("B3", val_b3), ("B4", val_b4), ("B5", val_b5)]:
            points.append(CompositePoint(
                campus=campus,
                bimestre=b,
                bimestre_label=BIMESTRE_LABELS[b],
                indice=v,
                tipo="Proyección"
            ))

    # 4. Proyección Global para B4 y B5
    for b in ["B4", "B5"]:
        num = sum(campus_indices[c][b] * MATRICULA_CAMPUS[c] for c in MATRICULA_CAMPUS)
        den = sum(MATRICULA_CAMPUS.values())
        g_val = round(num / den, 2)
        global_indices[b] = g_val

    for b in ["B3", "B4", "B5"]:
        points.append(CompositePoint(
            campus="Global",
            bimestre=b,
            bimestre_label=BIMESTRE_LABELS[b],
            indice=global_indices[b],
            tipo="Proyección"
        ))

    # 5. Evaluación de Semáforo Ejecutivo
    global_b3 = global_indices["B3"]
    campus_status: Dict[str, CampusStatus] = {}

    for c in MATRICULA_CAMPUS:
        idx_actual = campus_indices[c]["B3"]
        idx_b5 = campus_indices[c]["B5"]
        diff = round(idx_actual - global_b3, 2)

        if idx_b5 < 85.0 or diff < -10.0:
            estado = "risk"
            color_hex = "#ef4444"
            motivo = "Proyección B5 < 85%" if idx_b5 < 85.0 else "Más de 10 pts por debajo de Global"
        elif diff < -1.0:
            estado = "warning"
            color_hex = "#f59e0b"
            motivo = f"{abs(diff):.1f}% por debajo de Global"
        else:
            estado = "ok"
            color_hex = "#10b981"
            motivo = "Supera el promedio Global"

        campus_status[c] = CampusStatus(
            indice_actual=idx_actual,
            indice_b5=idx_b5,
            global_b3=global_b3,
            diff=diff,
            estado=estado,
            color_hex=color_hex,
            motivo=motivo
        )

    campus_status["Global"] = CampusStatus(
        indice_actual=global_indices["B3"],
        indice_b5=global_indices["B5"],
        global_b3=global_b3,
        diff=0.0,
        estado="info",
        color_hex="#0f172a",
        motivo="Promedio Global"
    )

    return CompositeIndexResponse(
        ciclo_escolar=ciclo_escolar,
        points=points,
        status=campus_status
    )
