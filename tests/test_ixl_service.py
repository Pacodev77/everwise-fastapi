# tests/test_ixl_service.py

import pytest
import pandas as pd
from app.services.ixl_service import procesar_diagnostico_ixl, clasificar_nivel_ixl

def test_clasificar_nivel_ixl():
    assert clasificar_nivel_ixl(850.0) == "Avanzado (Dominio Alto)"
    assert clasificar_nivel_ixl(700.0) == "Competente (Dominio Medio)"
    assert clasificar_nivel_ixl(500.0) == "En Desarrollo (En Progreso)"
    assert clasificar_nivel_ixl(350.0) == "Requiere Intervención (< 400)"

def test_procesar_diagnostico_ixl():
    df_raw = pd.DataFrame({
        "Estudiante": ["Juan", "Ana", "Carlos", "Sofia"],
        "Puntaje": [350, 550, 750, 900]
    })
    summary = procesar_diagnostico_ixl(df_raw, campus="Nuevo Sur")
    
    assert summary.campus == "Nuevo Sur"
    assert summary.total_estudiantes == 4
    assert summary.puntaje_promedio == pytest.approx(637.5, abs=1e-1)
    assert len(summary.distribucion_rangos) == 4
