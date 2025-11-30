# src/db.py
import os
import sqlite3

# sqlite | sqlserver | oracle
ENGINE = os.getenv("DB_ENGINE", "sqlite").lower()


def get_conn():
    if ENGINE == "sqlite":
        base_dir = os.path.abspath(os.path.join(
            os.path.dirname(__file__), "..", "database"))
        os.makedirs(base_dir, exist_ok=True)
        db_path = os.path.join(base_dir, "proyecto.db")

        conn = sqlite3.connect(db_path, check_same_thread=False)
        conn.row_factory = sqlite3.Row  # devuelve dicts
        return conn

    # Otros motores omitidos (SQL Server / Oracle)
    raise RuntimeError("Solo SQLite está habilitado en este proyecto.")


# -------------------------------
#   CREACIÓN AUTOMÁTICA DE TABLAS
# -------------------------------
def init_db():
    conn = get_conn()
    cursor = conn.cursor()

    # Tabla usuarios
    cursor.execute("""
    CREATE TABLE IF NOT EXISTS usuarios (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        username TEXT UNIQUE NOT NULL,
        password TEXT NOT NULL
    )
    """)

    # Tabla órdenes de compra
    cursor.execute("""
    CREATE TABLE IF NOT EXISTS ordenes_compra (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        numero_orden TEXT UNIQUE,
        cliente TEXT,
        direccion TEXT,
        telefono TEXT,
        comuna TEXT,
        region TEXT,
        total REAL,
        items_json TEXT,
        creado_en TEXT,
        estado TEXT DEFAULT 'pendiente'
    )
    """)

    # Tabla boletas (ya usas boletas)
    cursor.execute("""
    CREATE TABLE IF NOT EXISTS boletas (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        numero_boleta TEXT UNIQUE,
        numero_orden TEXT,
        cliente TEXT,
        direccion TEXT,
        telefono TEXT,
        comuna TEXT,
        region TEXT,
        neto REAL,
        iva REAL,
        total REAL,
        total_items INTEGER,
        items_json TEXT,
        creado_en TEXT
    )
    """)

    # RF4 – Tabla facturas
    cursor.execute("""
    CREATE TABLE IF NOT EXISTS facturas (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        numero_factura TEXT UNIQUE,
        numero_orden TEXT,
        subtotal REAL,
        iva REAL,
        total REAL,
        estado TEXT DEFAULT 'facturada',
        fecha TEXT
    )
    """)

    # RF5 – Tabla envíos
    cursor.execute("""
    CREATE TABLE IF NOT EXISTS envios (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        numero_factura TEXT,
        fecha_envio TEXT,
        estado_envio TEXT DEFAULT 'despachado'
    )
    """)

    conn.commit()
    conn.close()


# Ejecuta init_db automáticamente al importar db.py
init_db()
