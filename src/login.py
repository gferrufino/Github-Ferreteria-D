import os
import sqlite3
import hashlib
import secrets
from typing import Optional, Tuple

DB_PATH = os.path.abspath(os.path.join(
    os.path.dirname(__file__), "..", "database", "proyecto.db"))


def get_conn():
    os.makedirs(os.path.dirname(DB_PATH), exist_ok=True)
    return sqlite3.connect(DB_PATH, check_same_thread=False)


def _hash_password(password: str, salt: str) -> str:
    return hashlib.sha256((salt + password).encode("utf-8")).hexdigest()


def create_tables():
    conn = get_conn()
    cur = conn.cursor()
    cur.execute("""
        CREATE TABLE IF NOT EXISTS usuarios (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            username TEXT UNIQUE NOT NULL,
            password_hash TEXT NOT NULL,
            salt TEXT NOT NULL,
            nombre TEXT
        );
    """)
    cur.execute("""
        CREATE TABLE IF NOT EXISTS ordenes_compra (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            numero_orden TEXT UNIQUE NOT NULL,
            cliente TEXT NOT NULL,
            direccion TEXT NOT NULL,
            telefono TEXT NOT NULL,
            comuna TEXT NOT NULL,
            region TEXT NOT NULL,
            items_json TEXT NOT NULL,
            total REAL NOT NULL,
            creado_en DATETIME DEFAULT CURRENT_TIMESTAMP
        );
    """)
    conn.commit()

    # Usuario admin por defecto
    cur.execute("SELECT COUNT(1) FROM usuarios WHERE username = ?", ("admin",))
    exists = cur.fetchone()[0]
    if not exists:
        salt = secrets.token_hex(16)
        pwd_hash = _hash_password("admin123", salt)
        cur.execute(
            "INSERT INTO usuarios (username, password_hash, salt, nombre) VALUES (?, ?, ?, ?)",
            ("admin", pwd_hash, salt, "Administrador"),
        )
        conn.commit()
    conn.close()


def create_user(username: str, password: str, nombre: Optional[str] = None) -> Tuple[bool, str]:
    try:
        conn = get_conn()
        cur = conn.cursor()
        salt = secrets.token_hex(16)
        pwd_hash = _hash_password(password, salt)
        cur.execute(
            "INSERT INTO usuarios (username, password_hash, salt, nombre) VALUES (?, ?, ?, ?)",
            (username, pwd_hash, salt, nombre),
        )
        conn.commit()
        return True, "Usuario creado"
    except sqlite3.IntegrityError:
        return False, "El usuario ya existe"
    except Exception as e:
        return False, f"Error al crear usuario: {e}"
    finally:
        conn.close()


def verify_login(username: str, password: str) -> bool:
    conn = get_conn()
    cur = conn.cursor()
    cur.execute(
        "SELECT password_hash, salt FROM usuarios WHERE username = ?", (username,))
    row = cur.fetchone()
    conn.close()
    if not row:
        return False
    stored_hash, salt = row
    return stored_hash == _hash_password(password, salt)
