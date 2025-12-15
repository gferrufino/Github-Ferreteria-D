import sys
sys.path.append("src")

import orden_compra as oc

def test_emitir_factura():
    facturas = oc.listar_facturas_pendientes_envio()
    if not facturas:
        assert True
        return

    f = facturas[0]
    assert f["total"] > 0
