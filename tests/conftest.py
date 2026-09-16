# tests/conftest.py

import pytest
from app.services.data_repository import DataRepository, DEFAULT_USERS

@pytest.fixture(scope="session")
def default_password_hash():
    repo = DataRepository()
    return repo.hash_password_bcrypt("123")

@pytest.fixture(autouse=True)
def reset_test_users(default_password_hash):
    """Restablece los usuarios por defecto con contraseña '123' y must_change_password=1 antes de cada prueba de forma rápida."""
    repo = DataRepository()
    with repo.get_connection() as conn:
        cursor = conn.cursor()
        for u, p, r, n, e in DEFAULT_USERS:
            cursor.execute(
                "UPDATE users SET password_hash = ?, must_change_password = 1 WHERE username = ?",
                (default_password_hash, u)
            )
        conn.commit()
