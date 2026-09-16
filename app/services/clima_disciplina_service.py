# app/services/clima_disciplina_service.py

import pandas as pd
from typing import Dict, List, Any

def resumir_clima_escolar(df_clima: pd.DataFrame) -> Dict[str, Any]:
    """Procesa encuestas de clima escolar y genera mapa de satisfacción por dimensión."""
    if df_clima is None or df_clima.empty:
        return {"satisfaccion_promedio": 0.0, "dimensiones": {}}

    num_cols = df_clima.select_dtypes(include=["number"]).columns
    dimensiones = {}
    for col in num_cols:
        dimensiones[col] = round(float(df_clima[col].mean()), 2)

    prom_gen = round(float(df_clima[num_cols].mean().mean()), 2) if len(num_cols) > 0 else 0.0
    return {
        "satisfaccion_promedio": prom_gen,
        "dimensiones": dimensiones
    }

def resumir_disciplina(df_casos: pd.DataFrame, df_cartas: pd.DataFrame) -> Dict[str, Any]:
    """Resume el conteo de incidentes de disciplina y cartas de compromiso."""
    total_casos = len(df_casos) if df_casos is not None and not df_casos.empty else 0
    total_cartas = len(df_cartas) if df_cartas is not None and not df_cartas.empty else 0

    gravedad = {}
    if df_casos is not None and not df_casos.empty and "Gravedad" in df_casos.columns:
        gravedad = df_casos["Gravedad"].value_counts().to_dict()

    return {
        "total_casos": total_casos,
        "total_cartas": total_cartas,
        "desglose_gravedad": gravedad
    }
