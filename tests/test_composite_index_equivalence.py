# tests/test_composite_index_equivalence.py

import pytest
import pandas as pd
from app.services.composite_index_service import calcular_indice_compuesto, MATRICULA_CAMPUS

# Copia canónica del motor original de Streamlit para verificar equivalencia directa
def generar_datos_indice_compuesto_legacy(df_master: pd.DataFrame = None, ciclo_escolar: str = "2025 - 2026"):
    raw_data = {
        "Misiones": [
            {"bimestre": "B1", "acad": 85.0, "ixl": 72.0, "prog": 78.0},
            {"bimestre": "B2", "acad": 86.5, "ixl": 76.0, "prog": 81.0},
            {"bimestre": "B3", "acad": 87.8, "ixl": 79.0, "prog": 84.0},
        ],
        "Nuevo Sur": [
            {"bimestre": "B1", "acad": 88.0, "ixl": 80.0, "prog": 82.0},
            {"bimestre": "B2", "acad": 89.2, "ixl": 83.0, "prog": 85.0},
            {"bimestre": "B3", "acad": 90.5, "ixl": 86.0, "prog": 88.0},
        ],
        "San Agustín": [
            {"bimestre": "B1", "acad": 78.0, "ixl": 65.0, "prog": 70.0},
            {"bimestre": "B2", "acad": 79.5, "ixl": 68.0, "prog": 73.0},
            {"bimestre": "B3", "acad": 80.8, "ixl": 71.0, "prog": 75.0},
        ]
    }
    records = []
    campus_indices = {"Misiones": {}, "Nuevo Sur": {}, "San Agustín": {}}
    for campus, b_list in raw_data.items():
        for item in b_list:
            b = item["bimestre"]
            idx_val = (item["acad"] * 0.50) + (item["ixl"] * 0.30) + (item["prog"] * 0.20)
            campus_indices[campus][b] = round(idx_val, 2)
            records.append({"campus": campus, "bimestre": b, "indice": round(idx_val, 2), "tipo": "Real"})

    global_indices = {}
    for b in ["B1", "B2", "B3"]:
        num = sum(campus_indices[c][b] * MATRICULA_CAMPUS[c] for c in MATRICULA_CAMPUS)
        den = sum(MATRICULA_CAMPUS.values())
        g_val = round(num / den, 2)
        global_indices[b] = g_val
        records.append({"campus": "Global", "bimestre": b, "indice": g_val, "tipo": "Real"})

    for campus in MATRICULA_CAMPUS:
        val_b2 = campus_indices[campus]["B2"]
        val_b3 = campus_indices[campus]["B3"]
        delta = val_b3 - val_b2
        val_b4 = round(val_b3 + delta, 2)
        val_b5 = round(val_b4 + delta, 2)
        campus_indices[campus]["B4"] = val_b4
        campus_indices[campus]["B5"] = val_b5
        for b, v in [("B3", val_b3), ("B4", val_b4), ("B5", val_b5)]:
            records.append({"campus": campus, "bimestre": b, "indice": v, "tipo": "Proyección"})

    for b in ["B4", "B5"]:
        num = sum(campus_indices[c][b] * MATRICULA_CAMPUS[c] for c in MATRICULA_CAMPUS)
        den = sum(MATRICULA_CAMPUS.values())
        g_val = round(num / den, 2)
        global_indices[b] = g_val

    for b in ["B3", "B4", "B5"]:
        records.append({"campus": "Global", "bimestre": b, "indice": global_indices[b], "tipo": "Proyección"})

    df_res = pd.DataFrame(records)

    global_b3 = global_indices["B3"]
    campus_status = {}
    for c in MATRICULA_CAMPUS:
        idx_actual = campus_indices[c]["B3"]
        idx_b5 = campus_indices[c]["B5"]
        diff = idx_actual - global_b3
        if idx_b5 < 85.0 or diff < -10.0:
            estado, color_hex, motivo = "risk", "#ef4444", "Proyección B5 < 85%" if idx_b5 < 85.0 else "Más de 10 pts por debajo de Global"
        elif diff < -1.0:
            estado, color_hex, motivo = "warning", "#f59e0b", f"{abs(diff):.1f}% por debajo de Global"
        else:
            estado, color_hex, motivo = "ok", "#10b981", "Supera el promedio Global"
        campus_status[c] = {"indice_actual": idx_actual, "indice_b5": idx_b5, "global_b3": global_b3, "diff": diff, "estado": estado, "color_hex": color_hex, "motivo": motivo}

    campus_status["Global"] = {"indice_actual": global_indices["B3"], "indice_b5": global_indices["B5"], "global_b3": global_b3, "diff": 0.0, "estado": "info", "color_hex": "#0f172a", "motivo": "Promedio Global"}
    return df_res, campus_status


def test_equivalencia_tres_campus_y_global():
    # Ejecutar ambos motores
    df_legacy, status_legacy = generar_datos_indice_compuesto_legacy(ciclo_escolar="2025 - 2026")
    response_fastapi = calcular_indice_compuesto(ciclo_escolar="2025 - 2026")

    # 1. Comparar los 3 campus + Global en todos los puntos
    for campus in ["Misiones", "Nuevo Sur", "San Agustín", "Global"]:
        for b in ["B1", "B2", "B3", "B4", "B5"]:
            pts_fastapi = [p.indice for p in response_fastapi.points if p.campus == campus and p.bimestre == b]
            pts_legacy = df_legacy[(df_legacy["campus"] == campus) & (df_legacy["bimestre"] == b)]["indice"].tolist()

            assert len(pts_fastapi) > 0, f"Falta punto {campus} {b} en FastAPI"
            assert len(pts_legacy) > 0, f"Falta punto {campus} {b} en Legacy"
            assert pts_fastapi[0] == pytest.approx(pts_legacy[0], abs=1e-2), f"Diferencia en {campus} {b}: {pts_fastapi[0]} vs {pts_legacy[0]}"

    # 2. Comparar el semáforo y la ponderación Global por matrícula
    for campus in ["Misiones", "Nuevo Sur", "San Agustín", "Global"]:
        st_fastapi = response_fastapi.status[campus]
        st_legacy = status_legacy[campus]

        assert st_fastapi.indice_actual == pytest.approx(st_legacy["indice_actual"], abs=1e-2)
        assert st_fastapi.indice_b5 == pytest.approx(st_legacy["indice_b5"], abs=1e-2)
        assert st_fastapi.global_b3 == pytest.approx(st_legacy["global_b3"], abs=1e-2)
        assert st_fastapi.estado == st_legacy["estado"]
