# tests/test_academic_service.py

import pytest
import io
import pandas as pd
from app.services.academic_service import (
    procesar_archivo_academico,
    InvalidFileFormatException,
    MissingSubjectColumnException
)

def test_procesar_archivo_academico_csv_valido():
    csv_content = "Alumno,Nivel,Matemáticas,Español,Language Arts\nJuan,Primaria,9.0,8.5,9.2\nMaria,Primaria,7.5,8.0,8.0\n"
    csv_bytes = csv_content.encode("utf-8")
    
    df, summary = procesar_archivo_academico(
        file_bytes=csv_bytes,
        filename="calificaciones_misiones.csv",
        campus="Misiones",
        ciclo_escolar="2025 - 2026",
        bimestre="B3"
    )

    assert len(df) == 2
    assert summary.total_alumnos == 2
    assert summary.campus == "Misiones"
    assert summary.promedio_matematicas == 8.25
    assert summary.promedio_espanol == 8.25

def test_procesar_archivo_academico_formato_invalido():
    bad_bytes = b"contenido invalido"
    with pytest.raises(InvalidFileFormatException):
        procesar_archivo_academico(
            file_bytes=bad_bytes,
            filename="archivo.txt",
            campus="San Agustín"
        )

def test_procesar_archivo_academico_columna_faltante():
    csv_content = "Alumno,Nivel,Historia\nJuan,Primaria,9.0\n"
    csv_bytes = csv_content.encode("utf-8")

    with pytest.raises(MissingSubjectColumnException) as exc_info:
        procesar_archivo_academico(
            file_bytes=csv_bytes,
            filename="incompleto.csv",
            campus="Nuevo Sur"
        )
    assert "Matemáticas" in str(exc_info.value)
