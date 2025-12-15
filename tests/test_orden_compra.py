import sys
sys.path.append("src")

import orden_compra as oc

def test_crear_orden_compra():
    items = [
        {"producto": "Martillo", "precio": 5000, "cantidad": 2}
    ]

    ok, msg, numero = oc.agregar_orden(
        cliente="Cliente Test",
        direccion="Calle 123",
        telefono="+56912345678",
        comuna="Santiago",
        region="RM",
        items=items,
        user_id=1
    )

    assert ok is True
    assert numero.startswith("OC-")
