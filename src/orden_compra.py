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
    conn.row_factory = sqlite3.Row
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
        user_id INTEGER,
        estado TEXT DEFAULT 'pendiente'
    );
    """)


def _ensure_boleta_schema(cur: sqlite3.Cursor):
    cur.execute("""
    CREATE TABLE IF NOT EXISTS boletas (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        numero_boleta TEXT UNIQUE,
        numero_orden TEXT
    );
    """)
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


def _ensure_facturas_schema(cur: sqlite3.Cursor):
    cur.execute("""
    CREATE TABLE IF NOT EXISTS facturas (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        numero_factura TEXT UNIQUE,
        numero_orden TEXT,
        subtotal REAL,
        iva REAL,
        total REAL,
        estado TEXT DEFAULT 'facturada',
        fecha TEXT
    );
    """)


def _ensure_envios_schema(cur: sqlite3.Cursor):
    cur.execute("""
    CREATE TABLE IF NOT EXISTS envios (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        numero_factura TEXT,
        fecha_envio TEXT,
        estado_envio TEXT DEFAULT 'despachado'
    );
    """)


def _ensure_schema(conn: sqlite3.Connection):
    cur = conn.cursor()
    _ensure_oc_schema(cur)
    _ensure_boleta_schema(cur)
    _ensure_facturas_schema(cur)
    _ensure_envios_schema(cur)
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

    if not items:
        return False, "Debes agregar al menos 1 producto.", None

    clean_items: List[Dict[str, Any]] = []
    for it in items:
        nombre = (it.get("producto") or "").strip()
        precio = float(it.get("precio", 0))
        cant = int(it.get("cantidad", 0))
        if not nombre or precio <= 0 or cant <= 0:
            return False, "Cada ítem debe tener nombre, precio>0 y cantidad>0.", None
        clean_items.append({"producto": nombre, "precio": precio, "cantidad": cant})

    _, neto = _sumar_items(clean_items)

    attempts = 3
    for i in range(attempts):
        conn = get_conn()
        try:
            _ensure_schema(conn)
            cur = conn.cursor()
            cur.execute("BEGIN IMMEDIATE;")
            numero_orden = numero_orden_preasignado or generar_numero_orden()
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
            try:
                conn.rollback()
            except:
                pass
            if "unique" in str(e).lower() and i < attempts - 1:
                time.sleep(0.05)
                continue
            return False, "Colisión de número de orden; intenta nuevamente.", None

        except Exception as e:
            try:
                conn.rollback()
            except:
                pass
            return False, f"Error al registrar orden: {e}", None

        finally:
            try:
                conn.close()
            except:
                pass

    return False, "No fue posible generar un número de orden único.", None


def listar_ordenes(limit: int = 100, user_id: Optional[int] = None) -> List[Dict[str, Any]]:
    conn = get_conn()
    try:
        _ensure_schema(conn)
        cur = conn.cursor()
        if user_id is None:
            cur.execute("""
                SELECT id, numero_orden, cliente, direccion, telefono, comuna, region,
                       items_json, total, creado_en, user_id
                FROM ordenes_compra
                ORDER BY creado_en DESC, id DESC
                LIMIT ?
            """, (int(limit),))
        else:
            cur.execute("""
                SELECT id, numero_orden, cliente, direccion, telefono, comuna, region,
                       items_json, total, creado_en, user_id
                FROM ordenes_compra
                WHERE user_id = ?
                ORDER BY creado_en DESC, id DESC
                LIMIT ?
            """, (int(user_id), int(limit)))

        rows = cur.fetchall()
        out = []

        for r in rows:
            try:
                items = json.loads(r["items_json"]) if r["items_json"] else []
            except:
                items = []

            out.append({
                "id": r["id"],
                "numero_orden": r["numero_orden"],
                "cliente": r["cliente"],
                "direccion": r["direccion"],
                "telefono": r["telefono"],
                "comuna": r["comuna"],
                "region": r["region"],
                "items": items,
                "total": float(r["total"]),
                "creado_en": r["creado_en"],
                "user_id": r["user_id"],
            })

        return out
    finally:
        conn.close()


def obtener_orden_por_numero(numero_orden: str) -> Optional[Dict[str, Any]]:
    conn = get_conn()
    try:
        _ensure_schema(conn)
        cur = conn.cursor()
        cur.execute("""
            SELECT id, numero_orden, cliente, direccion, telefono, comuna, region,
                   items_json, total, creado_en, user_id
            FROM ordenes_compra
            WHERE numero_orden = ?
        """, (numero_orden,))
        r = cur.fetchone()
        if not r:
            return None
        try:
            items = json.loads(r["items_json"]) if r["items_json"] else []
        except:
            items = []

        return {
            "id": r["id"], "numero_orden": r["numero_orden"], "cliente": r["cliente"],
            "direccion": r["direccion"], "telefono": r["telefono"], "comuna": r["comuna"],
            "region": r["region"], "items": items, "total": float(r["total"]),
            "creado_en": r["creado_en"], "user_id": r["user_id"]
        }
    finally:
        conn.close()


# ----------------- BOLETA -----------------
def crear_boleta_para_orden(numero_orden: str) -> Tuple[bool, str, Optional[str]]:
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

        items = json.loads(items_json) if items_json else []
        total_items, neto = _sumar_items(items)
        if abs(neto - float(neto_oc)) > 0.01:
            neto = float(neto_oc)

        iva = round(neto * IVA_RATE, 2)
        total = round(neto + iva, 2)

        numero_boleta = _generar_numero_boleta(cur)
        cur.execute("""
            INSERT INTO boletas
            (numero_boleta, numero_orden, user_id, cliente, direccion, telefono,
             comuna, region, items_json, total_items, neto, iva, total)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
        """, (
            numero_boleta, numero_orden, user_id, cliente, direccion, telefono,
            comuna, region, items_json, total_items, neto, iva, total
        ))

        conn.commit()
        return True, f"Boleta {numero_boleta} emitida.", numero_boleta
    except Exception as e:
        conn.rollback()
        return False, f"Error al emitir boleta: {e}", None
    finally:
        conn.close()


def obtener_boleta_por_orden(numero_orden: str) -> Optional[Dict[str, Any]]:
    conn = get_conn()
    try:
        _ensure_schema(conn)
        cur = conn.cursor()
        cur.execute("""
            SELECT *
            FROM boletas
            WHERE numero_orden = ?
            ORDER BY id DESC
            LIMIT 1
        """, (numero_orden,))
        r = cur.fetchone()
        if not r:
            return None
        try:
            items = json.loads(r["items_json"]) if r["items_json"] else []
        except:
            items = []

        return {
            "numero_boleta": r["numero_boleta"],
            "numero_orden": r["numero_orden"],
            "user_id": r["user_id"],
            "cliente": r["cliente"],
            "direccion": r["direccion"],
            "telefono": r["telefono"],
            "comuna": r["comuna"],
            "region": r["region"],
            "items": items,
            "total_items": r["total_items"],
            "neto": r["neto"],
            "iva": r["iva"],
            "total": r["total"],
            "creado_en": r["creado_en"],
        }
    finally:
        conn.close()


# ===========================
# BOLETA → HTML imprimible
# ===========================
def _fmt_chl(n: float) -> str:
    try:
        return f"${int(round(float(n))):,}".replace(",", ".")
    except Exception:
        return str(n)


def boleta_a_html(boleta: Dict[str, any]) -> str:
    rows = []
    for it in boleta.get("items", []):
        producto = it.get("producto", "")
        cant = int(it.get("cantidad", 0))
        precio = float(it.get("precio", 0))
        rows.append(
            f"<tr><td>{producto}</td>"
            f"<td style='text-align:right'>{cant}</td>"
            f"<td style='text-align:right'>{_fmt_chl(precio)}</td></tr>"
        )
    rows_html = "\n".join(rows) or "<tr><td colspan='3'>(Sin ítems)</td></tr>"

    html = f"""<!doctype html>
<html><head>
<meta charset="utf-8">
<title>Boleta {boleta['numero_boleta']}</title>
<style>
  body {{ font-family: Arial, sans-serif; margin: 24px; }}
  h1 {{ margin-bottom: 4px; }}
  .small {{ color: #555; }}
  table {{ width: 100%; border-collapse: collapse; margin-top: 16px; }}
  th, td {{ border-bottom: 1px solid #eee; padding: 8px; }}
  tfoot td {{ border-top: 2px solid #333; font-weight: bold; }}
</style>
</head><body>
  <h1>Boleta {boleta['numero_boleta']}</h1>
  <div class="small">Orden: {boleta['numero_orden']} &nbsp;&nbsp;|&nbsp;&nbsp; Fecha: {boleta['creado_en']}</div>
  <p><strong>Cliente:</strong> {boleta['cliente']}<br>
     <strong>Dirección:</strong> {boleta['direccion']}, {boleta['comuna']}, {boleta['region']}<br>
     <strong>Teléfono:</strong> {boleta['telefono']}</p>

  <table>
    <thead>
      <tr><th>Producto</th><th style="text-align:right">Cant.</th><th style="text-align:right">Precio</th></tr>
    </thead>
    <tbody>
      {rows_html}
    </tbody>
    <tfoot>
      <tr><td colspan="2" style="text-align:right">Neto</td><td style="text-align:right">{_fmt_chl(boleta['neto'])}</td></tr>
      <tr><td colspan="2" style="text-align:right">IVA 19%</td><td style="text-align:right">{_fmt_chl(boleta['iva'])}</td></tr>
      <tr><td colspan="2" style="text-align:right">Total a pagar</td><td style="text-align:right">{_fmt_chl(boleta['total'])}</td></tr>
    </tfoot>
  </table>
</body></html>"""
    return html


# ================================================================
# ===================== FACTURAS (RF4) ============================
# ================================================================
def generar_numero_factura() -> str:
    conn = get_conn()
    cur = conn.cursor()
    _ensure_facturas_schema(cur)

    cur.execute("SELECT numero_factura FROM facturas")
    max_n = 0
    for (codigo,) in cur.fetchall():
        if codigo and codigo.startswith("FAC-"):
            try:
                n = int(codigo.split("-")[1])
                max_n = max(max_n, n)
            except:
                pass

    conn.close()
    return f"FAC-{max_n+1:04d}"


def crear_factura_para_orden(numero_orden: str):
    boleta = obtener_boleta_por_orden(numero_orden)
    if not boleta:
        return False, "Esta orden no tiene boleta asociada.", None

    subtotal = float(boleta["neto"])
    iva = float(boleta["iva"])
    total = float(boleta["total"])
    fecha = boleta["creado_en"]

    numero_factura = generar_numero_factura()

    conn = get_conn()
    cur = conn.cursor()
    _ensure_facturas_schema(cur)

    cur.execute("""
        INSERT INTO facturas (numero_factura, numero_orden, subtotal, iva, total, estado, fecha)
        VALUES (?, ?, ?, ?, ?, 'facturada', ?)
    """, (numero_factura, numero_orden, subtotal, iva, total, fecha))

    conn.commit()
    conn.close()

    return True, "Factura emitida correctamente.", numero_factura


def listar_facturas_pendientes_envio():
    conn = get_conn()
    cur = conn.cursor()
    _ensure_facturas_schema(cur)

    cur.execute("""
        SELECT numero_factura, numero_orden, subtotal, iva, total, estado, fecha
        FROM facturas
        WHERE estado = 'facturada'
    """)

    rows = cur.fetchall()
    conn.close()

    out = []
    for r in rows:
        out.append({
            "numero_factura": r["numero_factura"],
            "numero_orden": r["numero_orden"],
            "subtotal": r["subtotal"],
            "iva": r["iva"],
            "total": r["total"],
            "estado": r["estado"],
            "fecha": r["fecha"],
        })
    return out

def obtener_factura_por_numero(numero_factura: str):
    conn = get_conn()
    cur = conn.cursor()
    cur.execute("""
        SELECT numero_factura, numero_orden, subtotal, iva, total, estado, fecha
        FROM facturas
        WHERE numero_factura = ?
    """, (numero_factura,))
    r = cur.fetchone()
    conn.close()

    if not r:
        return None

    # Necesitamos los ítems y datos del cliente → vienen de la boleta
    boleta = obtener_boleta_por_orden(r["numero_orden"])

    return {
        "numero_factura": r["numero_factura"],
        "numero_orden": r["numero_orden"],
        "subtotal": r["subtotal"],
        "iva": r["iva"],
        "total": r["total"],
        "fecha": r["fecha"],
        "estado": r["estado"],
        "cliente": boleta["cliente"],
        "direccion": boleta["direccion"],
        "telefono": boleta["telefono"],
        "comuna": boleta["comuna"],
        "region": boleta["region"],
        "items": boleta["items"],
    }

def obtener_orden_por_factura(numero_factura: str):
    conn = get_conn()
    cur = conn.cursor()
    cur.execute("""
        SELECT numero_orden FROM facturas
        WHERE numero_factura = ?
    """, (numero_factura,))
    r = cur.fetchone()
    if not r:
        conn.close()
        return None

    numero_orden = r[0]

    # Recuperamos datos completos de la orden
    cur.execute("""
        SELECT cliente, direccion, comuna, region, telefono
        FROM ordenes_compra
        WHERE numero_orden = ?
    """, (numero_orden,))
    row = cur.fetchone()
    conn.close()

    if not row:
        return None

    return {
        "numero_orden": numero_orden,
        "cliente": row[0],
        "direccion": row[1],
        "comuna": row[2],
        "region": row[3],
        "telefono": row[4]
    }


# ================================================================
# ===================== ENVÍOS (RF5) =============================
# ================================================================
def registrar_envio(numero_factura: str):
    conn = get_conn()
    cur = conn.cursor()
    _ensure_envios_schema(cur)

    fecha_envio = time.strftime("%Y-%m-%d %H:%M:%S")

    cur.execute("""
        INSERT INTO envios (numero_factura, fecha_envio, estado_envio)
        VALUES (?, ?, 'despachado')
    """, (numero_factura, fecha_envio))

    cur.execute("""
        UPDATE facturas
        SET estado = 'despachada'
        WHERE numero_factura = ?
    """, (numero_factura,))

    conn.commit()
    conn.close()

    return True, "Producto despachado correctamente."
