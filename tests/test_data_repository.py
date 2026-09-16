# tests/test_data_repository.py

import pytest
import os
import sqlite3
from app.services.data_repository import DataRepository
from app.models.audit import AuditLogEntry

@pytest.fixture
def temp_repo(tmp_path):
    db_file = str(tmp_path / "test_everwise.db")
    repo = DataRepository(db_path=db_file)
    return repo

def test_user_seeding_and_auth(temp_repo):
    user = temp_repo.get_user("director")
    assert user is not None
    assert user.role == "General"
    assert user.name == "Director General"

    # Probar migración transparente de contraseña '123' a bcrypt
    is_valid = temp_repo.verify_password_and_migrate("director", "123", user.password_hash)
    assert is_valid is True

    # Consultar de nuevo para verificar que el hash se actualizó
    updated_user = temp_repo.get_user("director")
    assert updated_user.password_hash != "123"
    assert updated_user.password_hash.startswith("$2b$") or updated_user.password_hash.startswith("$2a$")

def test_audit_logs(temp_repo):
    entry = AuditLogEntry(
        usuario="misiones",
        accion="UPLOAD_ACADEMIC",
        detalle="Archivo calificaciones_b3.xlsx subido",
        campus="Misiones",
        ciclo_escolar="2025 - 2026"
    )
    temp_repo.add_audit_log(entry)

    logs = temp_repo.get_audit_logs(limit=10, ciclo_escolar="2025 - 2026")
    assert len(logs) == 1
    assert logs[0]["Usuario"] == "misiones"
    assert logs[0]["Acción"] == "UPLOAD_ACADEMIC"
    assert logs[0]["Campus"] == "Misiones"
