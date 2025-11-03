import os
import sqlite3
import hashlib
import secrets
from typing import Optional, Tuple, Dict, Any, List

DB_PATH = os.path.abspath(os.path.join(
    os.path.dirname(__file__), "..", "database", "proyecto.db"))

def get_conn():
    os.makedirs(os.path.dirname(DB_PATH), exist_ok=True)
    conn = sqlite3.connect(DB_PATH, check_same_thread=False)
    conn.execute("PRAGMA foreign_keys = ON;")
    return conn

def _hash_password(password: str, salt: str) -> str:
    return hashlib.sha256((salt + password).encode("utf-8")).hexdigest()

def _ensure_schema():
    conn = get_conn()
    cur = conn.cursor()
    try:
        cur.execute("""
        CREATE TABLE IF NOT EXISTS usuarios (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            username TEXT UNIQUE NOT NULL,
            password_hash TEXT NOT NULL,
            salt TEXT NOT NULL,
            nombre TEXT,
            role TEXT NOT NULL DEFAULT 'user'
        );
        """)
        cols = [r[1] for r in cur.execute("PRAGMA table_info(usuarios);").fetchall()]
        if "role" not in cols:
            cur.execute("ALTER TABLE usuarios ADD COLUMN role TEXT NOT NULL DEFAULT 'user';")

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
        cols_oc = [r[1] for r in cur.execute("PRAGMA table_info(ordenes_compra);").fetchall()]
        if "user_id" not in cols_oc:
            cur.execute("ALTER TABLE ordenes_compra ADD COLUMN user_id INTEGER;")

        conn.commit()

        cur.execute("SELECT COUNT(1) FROM usuarios WHERE username=?", ("admin",))
        if cur.fetchone()[0] == 0:
            salt = secrets.token_hex(16)
            pwd_hash = _hash_password("admin123", salt)
            cur.execute(
                "INSERT INTO usuarios (username, password_hash, salt, nombre, role) VALUES (?, ?, ?, ?, ?)",
                ("admin", pwd_hash, salt, "Administrador", "admin"),
            )
            conn.commit()
    finally:
        cur.close()
        conn.close()

def create_tables():
    _ensure_schema()

def get_user_by_username(username: str) -> Optional[Dict[str, Any]]:
    conn = get_conn()
    cur = conn.cursor()
    try:
        cur.execute("SELECT id, username, password_hash, salt, nombre, role FROM usuarios WHERE username=?", (username,))
        row = cur.fetchone()
        if not row:
            return None
        return {"id": row[0], "username": row[1], "password_hash": row[2], "salt": row[3], "nombre": row[4], "role": row[5]}
    finally:
        cur.close()
        conn.close()

def get_user_by_id(user_id: int) -> Optional[Dict[str, Any]]:
    conn = get_conn()
    cur = conn.cursor()
    try:
        cur.execute("SELECT id, username, password_hash, salt, nombre, role FROM usuarios WHERE id=?", (user_id,))
        row = cur.fetchone()
        if not row:
            return None
        return {"id": row[0], "username": row[1], "password_hash": row[2], "salt": row[3], "nombre": row[4], "role": row[5]}
    finally:
        cur.close()
        conn.close()

def list_users() -> List[Dict[str, Any]]:
    conn = get_conn()
    cur = conn.cursor()
    try:
        cur.execute("SELECT id, username, nombre, role FROM usuarios ORDER BY id ASC")
        return [{"id": r[0], "username": r[1], "nombre": r[2], "role": r[3]} for r in cur.fetchall()]
    finally:
        cur.close()
        conn.close()

def _create_user(username: str, password: str, nombre: Optional[str], role: str) -> Tuple[bool, str]:
    try:
        conn = get_conn()
        cur = conn.cursor()
        salt = secrets.token_hex(16)
        pwd_hash = _hash_password(password, salt)
        cur.execute(
            "INSERT INTO usuarios (username, password_hash, salt, nombre, role) VALUES (?, ?, ?, ?, ?)",
            (username, pwd_hash, salt, nombre, role),
        )
        conn.commit()
        return True, "Usuario creado"
    except sqlite3.IntegrityError:
        return False, "El usuario ya existe"
    except Exception as e:
        return False, f"Error al crear usuario: {e}"
    finally:
        try:
            cur.close()
            conn.close()
        except:
            pass

def create_user_admin(username: str, password: str, nombre: Optional[str], role: str = "user") -> Tuple[bool, str]:
    return _create_user(username, password, nombre, role)

def register_user(username: str, password: str, nombre: Optional[str]) -> Tuple[bool, str]:
    return _create_user(username, password, nombre, role="user")

def verify_login(username: str, password: str) -> Optional[Dict[str, Any]]:
    user = get_user_by_username(username)
    if not user:
        return None
    stored_hash, salt = user["password_hash"], user["salt"]
    if stored_hash == _hash_password(password, salt):
        return {k: user[k] for k in ("id", "username", "nombre", "role")}
    return None

def update_user(user_id: int, username: str, nombre: Optional[str], role: str) -> Tuple[bool, str]:
    try:
        conn = get_conn()
        cur = conn.cursor()
        cur.execute(
            "UPDATE usuarios SET username=?, nombre=?, role=? WHERE id=?",
            (username, nombre, role, user_id),
        )
        if cur.rowcount == 0:
            conn.rollback()
            return False, "Usuario no encontrado"
        conn.commit()
        return True, "Usuario actualizado"
    except sqlite3.IntegrityError:
        return False, "El nombre de usuario ya está en uso"
    except Exception as e:
        return False, f"Error al actualizar: {e}"
    finally:
        try:
            cur.close()
            conn.close()
        except:
            pass

def reset_password(user_id: int, new_password: str) -> Tuple[bool, str]:
    if not new_password:
        return False, "La nueva contraseña no puede estar vacía"
    try:
        conn = get_conn()
        cur = conn.cursor()
        salt = secrets.token_hex(16)
        pwd_hash = _hash_password(new_password, salt)
        cur.execute(
            "UPDATE usuarios SET password_hash=?, salt=? WHERE id=?",
            (pwd_hash, salt, user_id),
        )
        if cur.rowcount == 0:
            conn.rollback()
            return False, "Usuario no encontrado"
        conn.commit()
        return True, "Contraseña actualizada"
    except Exception as e:
        return False, f"Error al actualizar contraseña: {e}"
    finally:
        try:
            cur.close()
            conn.close()
        except:
            pass
