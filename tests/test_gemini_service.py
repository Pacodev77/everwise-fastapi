# tests/test_gemini_service.py

import pytest
from app.services.gemini_service import generar_recomendaciones_ejecutivas
from app.models.academic import AcademicBlockSummary

def test_generar_recomendaciones_ejecutivas_fallback():
    summary = AcademicBlockSummary(
        bloque="B3",
        campus="Misiones",
        ciclo_escolar="2025 - 2026",
        total_alumnos=180,
        promedio_matematicas=7.8,
        promedio_espanol=8.9,
        promedio_language_arts=8.5,
        pct_en_desempeno=70.0
    )
    res = generar_recomendaciones_ejecutivas(
        summary=summary,
        asistencia_promedio=0.94,
        campus="Misiones",
        api_key=""  # Forzar fallback local
    )

    assert "mantener" in res
    assert "mejorar" in res
    assert "modificar" in res
    assert len(res["mantener"]) > 0
    assert len(res["mejorar"]) > 0
