import os
import json
import sqlite3
from typing import List, Dict, Any, Tuple

DB_PATH = os.path.abspath(os.path.join(
    os.path.dirname(__file__), "..", "database", "proyecto.db"))


def get_conn():
    return sqlite3.connect(DB_PATH, check_same_thread=False)

# 🔢 Generar automáticamente el siguiente número de orden


def generar_numero_orden() -> str:
    conn = get_conn()
    cur = conn.cursor()
    cur.execute(
        "SELECT numero_orden FROM ordenes_compra ORDER BY id DESC LIMIT 1")
    row = cur.fetchone()
    conn.close()

    if not row or not row[0]:
        return "OC-0001"
    else:
        ultimo = row[0]
        try:
            num = int(ultimo.split("-")[1])
        except:
            num = 0
        return f"OC-{num + 1:04d}"


def agregar_orden(cliente: str, direccion: str, telefono: str,
                  comuna: str, region: str, items: List[Dict[str, Any]]) -> Tuple[bool, str]:
    """Inserta una orden en la tabla ordenes_compra con número automático."""
    try:
        numero_orden = generar_numero_orden()
        total = 0.0
        for it in items:
            precio = float(it.get("precio", 0))
            cantidad = int(it.get("cantidad", 1))
            total += precio * cantidad

        conn = get_conn()
        cur = conn.cursor()
        cur.execute(
            """
            INSERT INTO ordenes_compra (numero_orden, cliente, direccion, telefono, comuna, region, items_json, total)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?)
            """,
            (numero_orden, cliente, direccion, telefono, comuna,
             region, json.dumps(items, ensure_ascii=False), total),
        )
        conn.commit()
        return True, f"Orden {numero_orden} registrada correctamente"
    except sqlite3.IntegrityError:
        return False, "El número de orden ya existe"
    except Exception as e:
        return False, f"Error al registrar orden: {e}"
    finally:
        try:
            conn.close()
        except:
            pass


def listar_ordenes(limit: int = 100) -> List[Dict[str, Any]]:
    conn = get_conn()
    cur = conn.cursor()
    cur.execute(
        """
        SELECT id, numero_orden, cliente, direccion, telefono, comuna, region, items_json, total, creado_en
        FROM ordenes_compra ORDER BY creado_en DESC LIMIT ?
        """,
        (limit,),
    )
    rows = cur.fetchall()
    conn.close()
    result = []
    for r in rows:
        result.append({
            "id": r[0],
            "numero_orden": r[1],
            "cliente": r[2],
            "direccion": r[3],
            "telefono": r[4],
            "comuna": r[5],
            "region": r[6],
            "items": json.loads(r[7]),
            "total": r[8],
            "creado_en": r[9],
        })
    return result
