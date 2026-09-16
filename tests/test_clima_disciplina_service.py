# tests/test_clima_disciplina_service.py

import pytest
import pandas as pd
from app.services.clima_disciplina_service import resumir_clima_escolar, resumir_disciplina

def test_resumir_clima_escolar():
    df_clima = pd.DataFrame({
        "Instalaciones": [4.5, 4.0],
        "Docentes": [4.8, 4.6]
    })
    res = resumir_clima_escolar(df_clima)

    assert res["satisfaccion_promedio"] == pytest.approx(4.475, abs=1e-2)
    assert res["dimensiones"]["Instalaciones"] == 4.25
    assert res["dimensiones"]["Docentes"] == 4.7

def test_resumir_disciplina():
    df_casos = pd.DataFrame({"Gravedad": ["Leve", "Grave", "Leve"]})
    df_cartas = pd.DataFrame({"ID": [1, 2]})
    res = resumir_disciplina(df_casos, df_cartas)

    assert res["total_casos"] == 3
    assert res["total_cartas"] == 2
    assert res["desglose_gravedad"]["Leve"] == 2
