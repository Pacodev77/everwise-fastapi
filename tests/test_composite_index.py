# tests/test_composite_index.py

import pytest
from app.services.composite_index_service import calcular_indice_compuesto
from app.models.composite_index import CompositeIndexResponse

def test_calcular_indice_compuesto():
    res = calcular_indice_compuesto(ciclo_escolar="2025 - 2026")
    
    assert isinstance(res, CompositeIndexResponse)
    assert res.ciclo_escolar == "2025 - 2026"
    assert len(res.points) > 0

    # Verificar que existen registros para Misiones, Nuevo Sur, San Agustín y Global
    campus_encontrados = set(p.campus for p in res.points)
    assert "Misiones" in campus_encontrados
    assert "Nuevo Sur" in campus_encontrados
    assert "San Agustín" in campus_encontrados
    assert "Global" in campus_encontrados

    # Verificar bimestres B1..B5
    bimestres_misiones = set(p.bimestre for p in res.points if p.campus == "Misiones")
    assert bimestres_misiones == {"B1", "B2", "B3", "B4", "B5"}

    # Verificar semáforo ejecutivo
    assert "Misiones" in res.status
    assert "Nuevo Sur" in res.status
    assert "San Agustín" in res.status
    assert "Global" in res.status

    m_status = res.status["Misiones"]
    assert m_status.estado in ["ok", "warning", "risk"]
    assert m_status.indice_actual > 0
    assert m_status.color_hex.startswith("#")
