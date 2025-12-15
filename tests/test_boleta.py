import sys
sys.path.append("src")

import orden_compra as oc

def test_crear_boleta_con_iva():
    items = [
        {"producto": "Taladro", "precio": 10000, "cantidad": 1}
    ]

    ok, _, numero_orden = oc.agregar_orden(
        cliente="Cliente Boleta",
        direccion="Av Siempre Viva",
        telefono="+56912345678",
        comuna="Puente Alto",
        region="RM",
        items=items,
        user_id=1
    )

    assert ok

    ok, msg, numero_boleta = oc.crear_boleta_para_orden(numero_orden)
    assert ok is True

    boleta = oc.obtener_boleta_por_orden(numero_orden)
    assert boleta["iva"] > 0
    assert boleta["total"] > boleta["neto"]
