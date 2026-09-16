# tests/test_audit_service.py

import pytest
from app.services.audit_service import registrar_evento_auditoria, obtener_bitacora_auditoria
from app.services.data_repository import DataRepository

def test_audit_service_flow(tmp_path):
    db_file = str(tmp_path / "test_audit.db")
    repo = DataRepository(db_path=db_file)

    registrar_evento_auditoria(
        usuario="sanagustin",
        accion="UPLOAD_FILE",
        detalle="Subida de diagnósticos IXL",
        campus="San Agustín",
        ciclo_escolar="2025 - 2026",
        repo=repo
    )

    bitacora = obtener_bitacora_auditoria(limit=10, ciclo_escolar="2025 - 2026", repo=repo)
    assert len(bitacora) == 1
    assert bitacora[0]["Usuario"] == "sanagustin"
    assert bitacora[0]["Acción"] == "UPLOAD_FILE"
