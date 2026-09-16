# tests/test_asistencia_service.py

import pytest
import pandas as pd
from app.services.asistencia_service import calcular_asistencia_global

def test_calcular_asistencia_global():
    data_input = {
        "Misiones": {"niveles": pd.DataFrame({"Nivel": ["Primaria"], "Asistencia": [0.95]}), "staff": 0.90},
        "Nuevo Sur": {"niveles": pd.DataFrame({"Nivel": ["Primaria"], "Asistencia": [0.92]}), "staff": 0.88},
        "San Agustín": {"niveles": pd.DataFrame({"Nivel": ["Primaria"], "Asistencia": [0.90]}), "staff": 0.85}
    }
    res = calcular_asistencia_global(data_input)

    assert "niveles" in res
    assert "staff" in res
    assert "promedio_global" in res
    assert res["promedio_global"] > 0.90
    assert len(res["niveles"]) == 3
