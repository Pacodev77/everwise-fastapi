# app/services/asistencia_service.py

import pandas as pd
from typing import Dict, List, Optional, Any

MATRICULA_CAMPUS: Dict[str, int] = {
    "Misiones": 180,
    "Nuevo Sur": 150,
    "San Agustín": 170
}

def calcular_asistencia_global(
    asistencia_campus: Dict[str, Dict[str, Any]]
) -> Dict[str, Any]:
    """
    Calcula la agregación global de asistencia ponderada por matrícula a partir de los datos de cada campus.
    
    Cada entrada en asistencia_campus contiene:
    - 'niveles': DataFrame con columnas ['Nivel', 'Asistencia']
    - 'staff': Promedio de asistencia del personal (float)
    """
    niveles_agg: List[Dict[str, Any]] = []
    staff_agg: List[float] = []

    for campus_name in ["Misiones", "Nuevo Sur", "San Agustín"]:
        if campus_name in asistencia_campus and isinstance(asistencia_campus[campus_name], dict):
            data = asistencia_campus[campus_name]
            df_niveles = data.get("niveles")
            if isinstance(df_niveles, pd.DataFrame) and not df_niveles.empty and "Asistencia" in df_niveles.columns:
                mean_val = float(df_niveles["Asistencia"].dropna().mean()) if not df_niveles["Asistencia"].dropna().empty else 0.0
                niveles_agg.append({"Nivel": campus_name, "Asistencia": mean_val})
            
            staff_val = data.get("staff", 0.85)
            if staff_val is not None:
                staff_agg.append(float(staff_val))

    if not niveles_agg:
        df_empty = pd.DataFrame(columns=["Nivel", "Asistencia", "Distribución"])
        return {"niveles": df_empty, "staff": 0.85, "promedio_global": 0.0}

    df_res = pd.DataFrame(niveles_agg)
    total_suma = df_res["Asistencia"].sum()
    df_res["Distribución"] = df_res["Asistencia"] / total_suma if total_suma > 0 else 0.0
    
    # Promedio global ponderado por matrícula
    num = sum(row["Asistencia"] * MATRICULA_CAMPUS.get(row["Nivel"], 150) for _, row in df_res.iterrows())
    den = sum(MATRICULA_CAMPUS.get(row["Nivel"], 150) for _, row in df_res.iterrows())
    prom_global = round(num / den, 4) if den > 0 else 0.0

    staff_prom = float(sum(staff_agg) / len(staff_agg)) if staff_agg else 0.85

    return {
        "niveles": df_res,
        "staff": round(staff_prom, 4),
        "promedio_global": prom_global
    }

def parse_asistencia_file(file_bytes: bytes, ciclo_escolar: str = "2025 - 2026", campus: str = "Global") -> pd.DataFrame:
    """Parsea bytes de asistencia y retorna un DataFrame con metadatos."""
    try:
        try:
            df = pd.read_csv(pd.io.common.BytesIO(file_bytes))
        except Exception:
            df = pd.read_excel(pd.io.common.BytesIO(file_bytes))
    except Exception as e:
        raise Exception(f"No se pudo parsear el archivo de asistencia: {str(e)}")

    if df.empty:
        return df

    df["ciclo_escolar"] = ciclo_escolar
    df["campus"] = campus
    return df
