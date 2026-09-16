# app/services/ixl_service.py

import pandas as pd
from typing import Dict, List, Tuple
from app.models.ixl import IXLSummary, IXLSubjectBand

def clasificar_nivel_ixl(score: float) -> str:
    """Clasifica el puntaje diagnóstico IXL (Escala 0-1000) en niveles de dominio."""
    if score >= 800:
        return "Avanzado (Dominio Alto)"
    elif score >= 600:
        return "Competente (Dominio Medio)"
    elif score >= 400:
        return "En Desarrollo (En Progreso)"
    else:
        return "Requiere Intervención (< 400)"

def procesar_diagnostico_ixl(
    df_raw: pd.DataFrame, 
    campus: str = "Misiones", 
    ciclo_escolar: str = "2025 - 2026"
) -> IXLSummary:
    """
    Procesa los datos de diagnóstico IXL por campus y ciclo.
    Calcula el puntaje promedio y la distribución en 4 bandas de dominio.
    """
    if df_raw is None or df_raw.empty:
        return IXLSummary(
            campus=campus,
            ciclo_escolar=ciclo_escolar,
            total_estudiantes=0,
            puntaje_promedio=0.0,
            nivel_general="Sin Datos",
            distribucion_rangos=[]
        )

    # Identificar columna de puntaje
    score_col = None
    for col in ["Puntaje", "Score", "IXL Score", "Overall Score", "Diagnóstico"]:
        if col in df_raw.columns:
            score_col = col
            break

    if not score_col:
        # Fallback a primera columna numérica
        num_cols = df_raw.select_dtypes(include=["number"]).columns
        if len(num_cols) > 0:
            score_col = num_cols[0]

    if not score_col:
        return IXLSummary(
            campus=campus,
            ciclo_escolar=ciclo_escolar,
            total_estudiantes=len(df_raw),
            puntaje_promedio=0.0,
            nivel_general="Formato no reconocido",
            distribucion_rangos=[]
        )

    scores = pd.to_numeric(df_raw[score_col], errors="coerce").dropna()
    total_st = len(scores)
    if total_st == 0:
        return IXLSummary(
            campus=campus,
            ciclo_escolar=ciclo_escolar,
            total_estudiantes=0,
            puntaje_promedio=0.0,
            nivel_general="Sin Datos",
            distribucion_rangos=[]
        )

    mean_score = float(scores.mean())
    nivel_gen = clasificar_nivel_ixl(mean_score)

    # Definir bandas
    b1 = len(scores[scores < 400])
    b2 = len(scores[(scores >= 400) & (scores < 600)])
    b3 = len(scores[(scores >= 600) & (scores < 800)])
    b4 = len(scores[scores >= 800])

    bandas = [
        IXLSubjectBand(rango="< 400 (Intervención)", alumnos_count=b1, porcentaje=round((b1/total_st)*100, 1)),
        IXLSubjectBand(rango="400 - 599 (En Desarrollo)", alumnos_count=b2, porcentaje=round((b2/total_st)*100, 1)),
        IXLSubjectBand(rango="600 - 799 (Competente)", alumnos_count=b3, porcentaje=round((b3/total_st)*100, 1)),
        IXLSubjectBand(rango="800 - 1000 (Avanzado)", alumnos_count=b4, porcentaje=round((b4/total_st)*100, 1)),
    ]

    return IXLSummary(
        campus=campus,
        ciclo_escolar=ciclo_escolar,
        total_estudiantes=total_st,
        puntaje_promedio=round(mean_score, 1),
        nivel_general=nivel_gen,
        distribucion_rangos=bandas
    )
