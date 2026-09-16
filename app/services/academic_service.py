# app/services/academic_service.py

import pandas as pd
from typing import Dict, List, Optional, Tuple, Any
from app.models.academic import SubjectGrade, LevelAcademicSummary, AcademicBlockSummary

class InvalidFileFormatException(Exception):
    """Excepción lanzada cuando la estructura del archivo subido no coincide con el formato esperado."""
    pass

class MissingSubjectColumnException(InvalidFileFormatException):
    """Excepción lanzada cuando faltan columnas obligatorias de asignaturas."""
    pass

REQUIRED_ACADEMIC_COLUMNS = ["Matemáticas", "Español"]

def procesar_archivo_academico(
    file_bytes: bytes, 
    filename: str, 
    campus: str = "Misiones", 
    ciclo_escolar: str = "2025 - 2026",
    bimestre: str = "B3"
) -> Tuple[pd.DataFrame, AcademicBlockSummary]:
    """
    Procesa un archivo Excel o CSV de calificaciones enviado por un campus.
    
    Valida explícitamente:
    - Formato válido de archivo (XLSX, XLS, CSV).
    - Presencia de columnas académicas obligatorias ('Matemáticas', 'Español').
    
    Calcula:
    - Promedio por asignatura.
    - Porcentaje de alumnos en nivel óptimo de desempeño (promedio >= 8.0 en materias clave).
    - Desglose por nivel educativo (Primaria, Secundaria, Preescolar).
    """
    try:
        if filename.endswith(".csv"):
            df = pd.read_csv(pd.io.common.BytesIO(file_bytes))
        elif filename.endswith((".xlsx", ".xls")):
            df = pd.read_excel(pd.io.common.BytesIO(file_bytes))
        else:
            raise InvalidFileFormatException(f"Formato de archivo no soportado: '{filename}'. Use .xlsx, .xls o .csv")
    except Exception as e:
        if isinstance(e, InvalidFileFormatException):
            raise
        raise InvalidFileFormatException(f"Error leyendo el archivo '{filename}': {str(e)}")

    if df.empty:
        raise InvalidFileFormatException(f"El archivo '{filename}' está vacío.")

    # Normalizar nombres de columnas
    df.columns = [str(c).strip() for c in df.columns]

    # Validar presencia de columnas obligatorias
    missing_cols = [c for c in REQUIRED_ACADEMIC_COLUMNS if c not in df.columns]
    if missing_cols:
        raise MissingSubjectColumnException(
            f"El archivo '{filename}' del campus {campus} no contiene las columnas requeridas: {missing_cols}. "
            f"Columnas encontradas: {list(df.columns)}"
        )

    # Asegurar columna Language Arts si no viene
    if "Language Arts" not in df.columns:
        df["Language Arts"] = df["Español"]

    # Convertir a float limpio
    for col in ["Matemáticas", "Español", "Language Arts"]:
        df[col] = pd.to_numeric(df[col], errors="coerce").fillna(0.0)

    total_alumnos = len(df)
    prom_math = float(df["Matemáticas"].mean()) if total_alumnos > 0 else 0.0
    prom_esp = float(df["Español"].mean()) if total_alumnos > 0 else 0.0
    prom_la = float(df["Language Arts"].mean()) if total_alumnos > 0 else 0.0

    # Condición de desempeño: >= 8.0 en las 3 materias
    df["en_desempeno"] = (df["Matemáticas"] >= 8.0) & (df["Español"] >= 8.0) & (df["Language Arts"] >= 8.0)
    pct_desempeno = float(df["en_desempeno"].mean()) * 100.0 if total_alumnos > 0 else 0.0

    # Agregación por Nivel si existe la columna
    niveles_summary: List[LevelAcademicSummary] = []
    if "Nivel" in df.columns:
        for niv_name, group in df.groupby("Nivel"):
            sub_count = len(group)
            sub_desem = float(group["en_desempeno"].mean()) * 100.0 if sub_count > 0 else 0.0
            niveles_summary.append(LevelAcademicSummary(
                nivel=str(niv_name),
                total_alumnos=sub_count,
                pct_desempeno=round(sub_desem, 1),
                promedio_matematicas=round(float(group["Matemáticas"].mean()), 1),
                promedio_espanol=round(float(group["Español"].mean()), 1),
                promedio_language_arts=round(float(group["Language Arts"].mean()), 1)
            ))

    summary = AcademicBlockSummary(
        bloque=bimestre,
        campus=campus,
        ciclo_escolar=ciclo_escolar,
        total_alumnos=total_alumnos,
        promedio_matematicas=round(prom_math, 2),
        promedio_espanol=round(prom_esp, 2),
        promedio_language_arts=round(prom_la, 2),
        pct_en_desempeno=round(pct_desempeno, 1),
        niveles=niveles_summary
    )

    return df, summary
