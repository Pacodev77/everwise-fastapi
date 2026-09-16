# app/services/gemini_service.py

import json
import os
from typing import Dict, List, Optional
from app.config import settings
from app.models.academic import AcademicBlockSummary

def generar_recomendaciones_ejecutivas(
    summary: Optional[AcademicBlockSummary] = None,
    asistencia_promedio: Optional[float] = None,
    campus: str = "Global",
    api_key: Optional[str] = None
) -> Dict[str, List[str]]:
    """
    Genera un Plan de Acción Retrospectivo Inteligente estructurado en 3 ejes:
    - mantentener: Fortalezas y logros con cifras exactas.
    - mejorar: Áreas de oportunidad y asignaturas a reforzar.
    - modificar: Intervenciones prioritarias o ajustes metodológicos.

    Utiliza la API de Google Gemini ('gemini-1.5-flash') si la API Key está disponible.
    De lo contrario, recurre a un motor local determinista basado en los datos reales.
    """
    key = api_key or settings.GEMINI_API_KEY
    contexto = f"Campus {campus}" if campus and campus != "Global" else "Red Multicampus Global"

    prom_m = summary.promedio_matematicas if summary else 8.5
    prom_e = summary.promedio_espanol if summary else 8.7
    prom_la = summary.promedio_language_arts if summary else 8.4
    total_alumnos = summary.total_alumnos if summary else 500
    bimestre = summary.bloque if summary else "B3"
    pct_desempeno = summary.pct_en_desempeno if summary else 75.0

    # 1. Intentar llamada a la API de Gemini AI
    if key:
        try:
            import google.generativeai as genai
            genai.configure(api_key=key)
            model = genai.GenerativeModel("gemini-1.5-flash")

            prompt = f"""
            Eres un consultor ejecutivo escolar de Everwise para Instituto Agustín. Analiza los siguientes datos del {contexto} (Bimestre {bimestre}, {total_alumnos} alumnos):
            - Promedio Matemáticas: {prom_m:.1f}/10
            - Promedio Español: {prom_e:.1f}/10
            - Promedio Language Arts: {prom_la:.1f}/10
            - % Alumnos en Nivel Óptimo (>= 8.0): {pct_desempeno:.1f}%
            - Asistencia Promedio: {f'{asistencia_promedio*100:.1f}%' if asistencia_promedio else 'Sin datos de asistencia'}

            Genera un plan de acción retrospectivo ejecutivo con recomendaciones concretas basándote en estos números exactos.
            Responde exclusivamente en formato JSON con la siguiente estructura (sin código markdown ni explicaciones adicionales):
            {{
                "mantener": ["Logro o fortaleza principal con números exactos"],
                "mejorar": ["Área de oportunidad en materia o ausentismo"],
                "modificar": ["Acción correctiva o ajuste pedagógico prioritario"]
            }}
            """
            response = model.generate_content(prompt)
            text = response.text.strip()
            if text.startswith("```json"):
                text = text[7:]
            if text.endswith("```"):
                text = text[:-3]
            data = json.loads(text.strip())
            return {
                "mantener": data.get("mantener", []),
                "mejorar": data.get("mejorar", []),
                "modificar": data.get("modificar", [])
            }
        except Exception:
            pass  # Recurrir al motor local

    # 2. Motor Local Resiliente (Heurística Determinista)
    recomendaciones: Dict[str, List[str]] = {
        "mantener": [],
        "mejorar": [],
        "modificar": []
    }

    # Evaluar materia más fuerte y más débil
    materias = [("Matemáticas", prom_m), ("Español", prom_e), ("Language Arts", prom_la)]
    materias_ord = sorted(materias, key=lambda x: x[1], reverse=True)
    mejor_mat, mejor_val = materias_ord[0]
    peor_mat, peor_val = materias_ord[-1]

    if pct_desempeno >= 65.0:
        recomendaciones["mantener"].append(
            f"Sostener la sólida tasa de desempeño global ({pct_desempeno:.1f}% en Bimestre {bimestre}) en {contexto}."
        )
    recomendaciones["mantener"].append(
        f"Consolidar la estrategia en {mejor_mat}, la cual registra el promedio más alto con {mejor_val:.1f}/10."
    )

    if peor_val < 8.0:
        recomendaciones["mejorar"].append(
            f"Reforzar {peor_mat} (promedio actual de {peor_val:.1f}/10) con talleres prácticos y repasos dirigidos."
        )
    else:
        recomendaciones["mejorar"].append(
            f"Mantener programas de aceleración académica para llevar el promedio de {peor_mat} por encima de 8.8/10."
        )

    if asistencia_promedio:
        if asistencia_promedio >= 0.92:
            recomendaciones["mantener"].append(
                f"Sostener la alta asistencia escolar del campus ({asistencia_promedio*100:.1f}%)."
            )
        else:
            recomendaciones["mejorar"].append(
                f"Optimizar el seguimiento a ausentismo (asistencia actual: {asistencia_promedio*100:.1f}%)."
            )

    if peor_val < 8.0:
        recomendaciones["modificar"].append(
            f"Modificar el esquema de evaluación y tutorías grupales en {peor_mat} al situarse por debajo de 8.0/10."
        )
    else:
        recomendaciones["modificar"].append(
            "Ajustar la frecuencia de repasos preventivos antes de los exámenes bimestrales para reducir variabilidad."
        )

    return recomendaciones
