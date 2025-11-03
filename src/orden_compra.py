from __future__ import annotations

import json
import re
import time
import sqlite3
from typing import List, Dict, Any, Tuple, Optional

DB_PATH = __import__("os").path.abspath(__import__("os").path.join(
    __import__("os").path.dirname(__file__), "..", "database", "proyecto.db"))

_OC_PREFIX = "OC-"
_OC_RE = re.compile(r"^OC-(\d{4,})$")
_BL_PREFIX = "BL-"
_BL_RE = re.compile(r"^BL-(\d{4,})$")

IVA_RATE = 0.19 

def get_conn():
    conn = sqlite3.connect(DB_PATH, check_same_thread=False)
    conn.execute("PRAGMA foreign_keys = ON;")
    return conn

# ----------------- SCHEMA -----------------
def _ensure_oc_schema(cur: sqlite3.Cursor):
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
        creado_en DATETIME DEFAULT CURRENT_TIMESTAMP,
        user_id INTEGER
    );
    """)

def _ensure_boleta_schema(cur: sqlite3.Cursor):
    # Asegura existencia de la tabla (si no existía)
    cur.execute("""
    CREATE TABLE IF NOT EXISTS boletas (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        numero_boleta TEXT UNIQUE,
        numero_orden TEXT
    );
    """)
    # Migra columnas faltantes (ADD COLUMN es compatible y no borra datos)
    cur.execute("PRAGMA table_info(boletas);")
    cols = {r[1] for r in cur.fetchall()}

    def add(col, decl):
        if col not in cols:
            cur.execute(f"ALTER TABLE boletas ADD COLUMN {col} {decl};")

    add("user_id", "INTEGER")
    add("cliente", "TEXT")
    add("direccion", "TEXT")
    add("telefono", "TEXT")
    add("comuna", "TEXT")
    add("region", "TEXT")
    add("items_json", "TEXT")
    add("total_items", "INTEGER")
    add("neto", "REAL")
    add("iva", "REAL")
    add("total", "REAL")
    add("creado_en", "DATETIME DEFAULT CURRENT_TIMESTAMP")

def _ensure_schema(conn: sqlite3.Connection):
    cur = conn.cursor()
    _ensure_oc_schema(cur)
    _ensure_boleta_schema(cur)
    conn.commit()

# ----------------- NUMERADORES -----------------
def _next_code(cur: sqlite3.Cursor, tabla: str, campo: str, pref: str, regex: re.Pattern) -> str:
    cur.execute(f"SELECT {campo} FROM {tabla}")
    max_n = 0
    for (code,) in cur.fetchall():
        if not code: 
            continue
        m = regex.match(code)
        if m:
            try:
                n = int(m.group(1))
                if n > max_n:
                    max_n = n
            except:
                pass
    return f"{pref}{(max_n + 1):04d}"

def generar_numero_orden() -> str:
    conn = get_conn()
    try:
        _ensure_schema(conn)
        cur = conn.cursor()
        return _next_code(cur, "ordenes_compra", "numero_orden", _OC_PREFIX, _OC_RE)
    finally:
        conn.close()

def _generar_numero_boleta(cur: sqlite3.Cursor) -> str:
    return _next_code(cur, "boletas", "numero_boleta", _BL_PREFIX, _BL_RE)

# ----------------- HELPERS -----------------
def _sumar_items(items: List[Dict[str, Any]]) -> Tuple[int, float]:
    total_items = 0
    neto = 0.0
    for it in items:
        q = int(it.get("cantidad", 0))
        p = float(it.get("precio", 0))
        total_items += q
        neto += q * p
    return total_items, neto

# ----------------- CRUD OC -----------------
def agregar_orden(
    cliente: str, direccion: str, telefono: str, comuna: str, region: str,
    items: List[Dict[str, Any]], user_id: Optional[int] = None,
    numero_orden_preasignado: Optional[str] = None
) -> Tuple[bool, str, Optional[str]]:
    """
    Inserta una OC. Retorna (ok, mensaje, numero_orden).
    total = NETO (sin IVA). La boleta hará el desglose con IVA.
    """
    if not items:
        return False, "Debes agregar al menos 1 producto.", None

    # Validación + normalización
    clean_items: List[Dict[str, Any]] = []
    for it in items:
        nombre = (it.get("producto") or "").strip()
        precio = float(it.get("precio", 0))
        cant = int(it.get("cantidad", 0))
        if not nombre or precio <= 0 or cant <= 0:
            return False, "Cada ítem debe tener nombre, precio>0 y cantidad>0.", None
        clean_items.append({"producto": nombre, "precio": precio, "cantidad": cant})

    # Neto de la OC (sin IVA)
    _, neto = _sumar_items(clean_items)

    attempts = 3
    for i in range(attempts):
        conn = get_conn()
        try:
            _ensure_schema(conn)
            cur = conn.cursor()
            cur.execute("BEGIN IMMEDIATE;")
            numero_orden = numero_orden_preasignado or _next_code(cur, "ordenes_compra", "numero_orden", _OC_PREFIX, _OC_RE)
            cur.execute("""
                INSERT INTO ordenes_compra
                (numero_orden, cliente, direccion, telefono, comuna, region, items_json, total, user_id)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
            """, (
                numero_orden, cliente.strip(), direccion.strip(), telefono.strip(),
                comuna.strip(), region.strip(), json.dumps(clean_items, ensure_ascii=False),
                neto, user_id
            ))
            conn.commit()
            return True, f"Orden {numero_orden} registrada correctamente", numero_orden
        except sqlite3.IntegrityError as e:
            try: conn.rollback()
            except: pass
            if "unique" in str(e).lower() and i < attempts - 1:
                time.sleep(0.05); continue
            return False, "Colisión de número de orden; intenta nuevamente.", None
        except Exception as e:
            try: conn.rollback()
            except: pass
            return False, f"Error al registrar orden: {e}", None
        finally:
            try: conn.close()
            except: pass
    return False, "No fue posible generar un número de orden único.", None

def listar_ordenes(limit: int = 100, user_id: Optional[int] = None) -> List[Dict[str, Any]]:
    conn = get_conn()
    try:
        _ensure_schema(conn)
        cur = conn.cursor()
        if user_id is None:
            cur.execute("""
                SELECT id, numero_orden, cliente, direccion, telefono, comuna, region, items_json, total, creado_en, user_id
                FROM ordenes_compra
                ORDER BY creado_en DESC, id DESC
                LIMIT ?
            """, (int(limit),))
        else:
            cur.execute("""
                SELECT id, numero_orden, cliente, direccion, telefono, comuna, region, items_json, total, creado_en, user_id
                FROM ordenes_compra
                WHERE user_id = ?
                ORDER BY creado_en DESC, id DESC
                LIMIT ?
            """, (int(user_id), int(limit)))
        rows = cur.fetchall()
        out: List[Dict[str, Any]] = []
        for r in rows:
            try:
                items = json.loads(r[7]) if r[7] else []
            except:
                items = []
            out.append({
                "id": r[0], "numero_orden": r[1], "cliente": r[2], "direccion": r[3],
                "telefono": r[4], "comuna": r[5], "region": r[6],
                "items": items, "total": float(r[8]), "creado_en": r[9], "user_id": r[10],
            })
        return out
    finally:
        try: conn.close()
        except: pass

def obtener_orden_por_numero(numero_orden: str) -> Optional[Dict[str, Any]]:
    conn = get_conn()
    try:
        _ensure_schema(conn)
        cur = conn.cursor()
        cur.execute("""
            SELECT id, numero_orden, cliente, direccion, telefono, comuna, region, items_json, total, creado_en, user_id
            FROM ordenes_compra
            WHERE numero_orden = ?
        """, (numero_orden,))
        r = cur.fetchone()
        if not r:
            return None
        try:
            items = json.loads(r[7]) if r[7] else []
        except:
            items = []
        return {
            "id": r[0], "numero_orden": r[1], "cliente": r[2], "direccion": r[3],
            "telefono": r[4], "comuna": r[5], "region": r[6],
            "items": items, "total": float(r[8]), "creado_en": r[9], "user_id": r[10],
        }
    finally:
        try: conn.close()
        except: pass

# ----------------- BOLETA (con IVA) -----------------
def crear_boleta_para_orden(numero_orden: str) -> Tuple[bool, str, Optional[str]]:
    """
    Crea boleta (BL-####) con desglose NETO, IVA (19%) y TOTAL.
    Copia datos de cliente y detalle de la OC.
    Retorna (ok, msg, numero_boleta).
    """
    conn = get_conn()
    try:
        _ensure_schema(conn)
        cur = conn.cursor()
        cur.execute("BEGIN IMMEDIATE;")

        cur.execute("""
            SELECT cliente, direccion, telefono, comuna, region, items_json, total, user_id
            FROM ordenes_compra
            WHERE numero_orden = ?
        """, (numero_orden,))
        row = cur.fetchone()
        if not row:
            conn.rollback()
            return False, "Orden no encontrada para emitir boleta.", None

        cliente, direccion, telefono, comuna, region, items_json, neto_oc, user_id = row
        # Aseguramos cálculo desde items por consistencia
        items = json.loads(items_json) if items_json else []
        total_items, neto = _sumar_items(items)
        # Si por alguna razón difiere del guardado en OC, usamos el calculado
        if abs(neto - float(neto_oc)) > 0.01:
            neto = float(neto_oc)

        iva = round(neto * IVA_RATE, 2)
        total = round(neto + iva, 2)

        numero_boleta = _generar_numero_boleta(cur)
        cur.execute("""
            INSERT INTO boletas
            (numero_boleta, numero_orden, user_id, cliente, direccion, telefono, comuna, region,
             items_json, total_items, neto, iva, total)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
        """, (
            numero_boleta, numero_orden, user_id, cliente, direccion, telefono, comuna, region,
            items_json, total_items, neto, iva, total
        ))
        conn.commit()
        return True, f"Boleta {numero_boleta} emitida.", numero_boleta
    except sqlite3.IntegrityError:
        try: conn.rollback()
        except: pass
        return False, "Ya existe una boleta con ese número.", None
    except Exception as e:
        try: conn.rollback()
        except: pass
        return False, f"Error al emitir boleta: {e}", None
    finally:
        try: conn.close()
        except: pass

def obtener_boleta_por_numero(numero_boleta: str) -> Optional[Dict[str, Any]]:
    conn = get_conn()
    try:
        _ensure_schema(conn)
        cur = conn.cursor()
        cur.execute("""
            SELECT numero_boleta, numero_orden, user_id, cliente, direccion, telefono, comuna, region,
                   items_json, total_items, neto, iva, total, creado_en
            FROM boletas
            WHERE numero_boleta = ?
        """, (numero_boleta,))
        r = cur.fetchone()
        if not r:
            return None
        try:
            items = json.loads(r[8]) if r[8] else []
        except:
            items = []
        return {
            "numero_boleta": r[0], "numero_orden": r[1], "user_id": r[2],
            "cliente": r[3], "direccion": r[4], "telefono": r[5], "comuna": r[6], "region": r[7],
            "items": items, "total_items": r[9], "neto": r[10], "iva": r[11],
            "total": r[12], "creado_en": r[13],
        }
    finally:
        try: conn.close()
        except: pass
def obtener_boleta_por_orden(numero_orden: str) -> Optional[Dict[str, Any]]:
    conn = get_conn()
    try:
        _ensure_schema(conn)
        cur = conn.cursor()
        # Si hubiera más de una, toma la última emitida
        cur.execute("""
            SELECT numero_boleta, numero_orden, user_id, cliente, direccion, telefono, comuna, region,
                   items_json, total_items, neto, iva, total, creado_en
            FROM boletas
            WHERE numero_orden = ?
            ORDER BY id DESC
            LIMIT 1
        """, (numero_orden,))
        r = cur.fetchone()
        if not r:
            return None
        try:
            items = json.loads(r[8]) if r[8] else []
        except:
            items = []
        return {
            "numero_boleta": r[0], "numero_orden": r[1], "user_id": r[2],
            "cliente": r[3], "direccion": r[4], "telefono": r[5], "comuna": r[6], "region": r[7],
            "items": items, "total_items": r[9], "neto": r[10], "iva": r[11],
            "total": r[12], "creado_en": r[13],
        }
    finally:
        try: conn.close()
        except: pass