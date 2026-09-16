# app/services/data_repository.py

import sqlite3
import os
import pandas as pd
from typing import List, Dict, Optional, Any, Tuple
import bcrypt
import hashlib
from app.config import settings
from app.models.audit import AuditLogEntry
from app.models.user import UserInDB

LEGACY_SALT = "everwise_crm_salt_2026"

DEFAULT_USERS = [
    ("director", "123", "General", "Director General", "admin@everwise.edu"),
    ("misiones", "123", "Misiones", "Coordinador Misiones", "misiones@everwise.edu"),
    ("nuevosur", "123", "Nuevo Sur", "Coordinador Nuevo Sur", "nuevosur@everwise.edu"),
    ("sanagustin", "123", "San Agustín", "Coordinador San Agustín", "sanagustin@everwise.edu"),
]

class DataRepository:
    def __init__(self, db_path: str = None):
        self.db_path = db_path or settings.DB_PATH
        self._ensure_db_dir()
        self.init_db()

    def _ensure_db_dir(self):
        db_dir = os.path.dirname(self.db_path)
        if db_dir:
            os.makedirs(db_dir, exist_ok=True)

    def get_connection(self) -> sqlite3.Connection:
        conn = sqlite3.connect(self.db_path, timeout=30.0)
        conn.row_factory = sqlite3.Row
        return conn

    @staticmethod
    def _hash_legacy_sha256(password: str) -> str:
        return hashlib.sha256((password + LEGACY_SALT).encode("utf-8")).hexdigest()

    @staticmethod
    def hash_password_bcrypt(password: str) -> str:
        pw_bytes = password.encode("utf-8")[:72]
        salt = bcrypt.gensalt()
        return bcrypt.hashpw(pw_bytes, salt).decode("utf-8")

    def verify_password_and_migrate(self, username: str, plain_password: str, stored_hash: str) -> bool:
        """
        Verifica la contraseña ingresada.
        Si la contraseña coincide con el esquema legacy SHA256 o '123',
        actualiza la base de datos automáticamente al nuevo hash seguro Bcrypt.
        """
        pw_bytes = plain_password.encode("utf-8")[:72]

        if stored_hash.startswith("$2b$") or stored_hash.startswith("$2a$") or stored_hash.startswith("$2y$"):
            try:
                if bcrypt.checkpw(pw_bytes, stored_hash.encode("utf-8")):
                    return True
            except Exception:
                pass

        # Verificar legacy SHA256 o password por defecto
        legacy_hash = self._hash_legacy_sha256(plain_password)
        if stored_hash == legacy_hash or (stored_hash == self._hash_legacy_sha256("123") and plain_password == "123") or stored_hash == "123":
            new_bcrypt_hash = self.hash_password_bcrypt(plain_password)
            self.update_user_password(username, new_bcrypt_hash)
            return True

        return False

    def init_db(self):
        """Inicializa las tablas base en SQLite si no existen."""
        with self.get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute("""
                CREATE TABLE IF NOT EXISTS users (
                    username TEXT PRIMARY KEY,
                    password_hash TEXT NOT NULL,
                    role TEXT NOT NULL,
                    name TEXT NOT NULL,
                    email TEXT,
                    is_active INTEGER DEFAULT 1,
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
                )
            """)
            cursor.execute("""
                CREATE TABLE IF NOT EXISTS audit_logs (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    usuario TEXT NOT NULL,
                    accion TEXT NOT NULL,
                    detalle TEXT NOT NULL,
                    campus TEXT,
                    ciclo_escolar TEXT,
                    timestamp TIMESTAMP DEFAULT CURRENT_TIMESTAMP
                )
            """)
            conn.commit()

            # Sembrar usuarios iniciales si la tabla está vacía
            for u, p, r, n, e in DEFAULT_USERS:
                cursor.execute("SELECT username FROM users WHERE username = ?", (u,))
                if not cursor.fetchone():
                    p_hash = self.hash_password_bcrypt(p)
                    cursor.execute(
                        "INSERT INTO users (username, password_hash, role, name, email) VALUES (?, ?, ?, ?, ?)",
                        (u, p_hash, r, n, e)
                    )
            conn.commit()

    def get_user(self, username: str) -> Optional[UserInDB]:
        with self.get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute(
                "SELECT username, password_hash, role, name, email, is_active FROM users WHERE username = ?",
                (username,)
            )
            row = cursor.fetchone()
            if row and row["is_active"] == 1:
                return UserInDB(
                    username=row["username"],
                    password_hash=row["password_hash"],
                    role=row["role"],
                    name=row["name"],
                    email=row["email"],
                    is_active=bool(row["is_active"])
                )
        return None

    def update_user_password(self, username: str, new_bcrypt_hash: str):
        with self.get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute(
                "UPDATE users SET password_hash = ? WHERE username = ?",
                (new_bcrypt_hash, username)
            )
            conn.commit()

    def add_audit_log(self, entry: AuditLogEntry):
        with self.get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute("""
                INSERT INTO audit_logs (usuario, accion, detalle, campus, ciclo_escolar, timestamp)
                VALUES (?, ?, ?, ?, ?, ?)
            """, (entry.usuario, entry.accion, entry.detalle, entry.campus, entry.ciclo_escolar, entry.timestamp))
            conn.commit()

    def get_audit_logs(self, limit: int = 100, ciclo_escolar: Optional[str] = None) -> List[Dict[str, Any]]:
        with self.get_connection() as conn:
            cursor = conn.cursor()
            if ciclo_escolar:
                cursor.execute("""
                    SELECT id, usuario as Usuario, accion as Acción, detalle as Detalle, 
                           campus as Campus, ciclo_escolar as 'Ciclo Escolar', timestamp as Timestamp
                    FROM audit_logs
                    WHERE ciclo_escolar = ?
                    ORDER BY id DESC LIMIT ?
                """, (ciclo_escolar, limit))
            else:
                cursor.execute("""
                    SELECT id, usuario as Usuario, accion as Acción, detalle as Detalle, 
                           campus as Campus, ciclo_escolar as 'Ciclo Escolar', timestamp as Timestamp
                    FROM audit_logs
                    ORDER BY id DESC LIMIT ?
                """, (limit,))
            rows = cursor.fetchall()
            return [dict(r) for r in rows]

    def read_table_dataframe(self, table_name: str, ciclo_escolar: Optional[str] = None, campus: Optional[str] = None) -> pd.DataFrame:
        """Lee una tabla completa de SQLite filtrando por ciclo_escolar y campus si aplican."""
        with self.get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute("SELECT name FROM sqlite_master WHERE type='table' AND name=?", (table_name,))
            if not cursor.fetchone():
                return pd.DataFrame()

            # Inspeccionar columnas
            cursor.execute(f"PRAGMA table_info({table_name})")
            cols = [col["name"] for col in cursor.fetchall()]

            query = f"SELECT * FROM {table_name} WHERE 1=1"
            params = []

            if ciclo_escolar and "ciclo_escolar" in cols:
                query += " AND ciclo_escolar = ?"
                params.append(ciclo_escolar)

            if campus and "campus" in cols and campus != "Global":
                query += " AND campus = ?"
                params.append(campus)

            df = pd.read_sql_query(query, conn, params=params)
            return df

    def save_dataframe_table(self, df: pd.DataFrame, table_name: str, if_exists: str = "append"):
        """Guarda un DataFrame en SQLite."""
        if df.empty:
            return
        with self.get_connection() as conn:
            df.to_sql(table_name, conn, if_exists=if_exists, index=False)
