import streamlit as st
import pandas as pd
import orden_compra as oc

def _fm(n):
    try:
        return f"${int(round(float(n))):,}".replace(",", ".")
    except:
        return str(n)

def emitir_factura_view():
    st.header("🧾 Emitir Factura")
    st.caption("Selecciona una orden con boleta para generar su factura con IVA y dejar registro.")

    # 1) Traer órdenes del usuario (o todas si admin, según tu lógica)
    ordenes = oc.listar_ordenes(limit=300, user_id=st.session_state.get("user_id"))

    # Solo permitir las que ya tienen boleta
    opciones = {}
    for o in ordenes:
        b = oc.obtener_boleta_por_orden(o["numero_orden"])
        if b:
            opciones[f"{o['numero_orden']} — {o['cliente']} — {o['creado_en']}"] = o["numero_orden"]

    if not opciones:
        st.info("No hay órdenes con boleta disponible para facturar.")
        return

    numero_orden = st.selectbox("Selecciona una orden", list(opciones.keys()))
    numero_orden = opciones[numero_orden]

    # 2) Vista previa: boleta / totales
    boleta = oc.obtener_boleta_por_orden(numero_orden)
    if not boleta:
        st.error("Esta orden no tiene boleta (no debería pasar).")
        return

    # Tabla de ítems
    items = boleta.get("items", [])
    df = pd.DataFrame([{
        "Producto": it.get("producto"),
        "Cantidad": int(it.get("cantidad", 0)),
        "Precio": _fm(it.get("precio", 0)),
        "Subtotal": _fm(float(it.get("precio", 0)) * int(it.get("cantidad", 0)))
    } for it in items])

    st.markdown("### Vista previa")
    c1, c2 = st.columns(2)
    with c1:
        st.write(f"**Cliente:** {boleta['cliente']}")
        st.write(f"**Teléfono:** {boleta['telefono']}")
    with c2:
        st.write(f"**Dirección:** {boleta['direccion']}, {boleta['comuna']}, {boleta['region']}")
        st.write(f"**Orden:** {boleta['numero_orden']} | **Boleta:** {boleta['numero_boleta']}")

    st.dataframe(df, use_container_width=True, hide_index=True)

    c3, c4, c5 = st.columns(3)
    c3.metric("Neto", _fm(boleta["neto"]))
    c4.metric("IVA (19%)", _fm(boleta["iva"]))
    c5.metric("Total", _fm(boleta["total"]))

    st.markdown("---")

    # 3) Evitar facturar 2 veces: si ya existe una factura para esa OC
    # (si no tienes función, hacemos check simple leyendo facturas y buscando OC)
    ya_facturada = False
    try:
        fact_pend = oc.listar_facturas_pendientes_envio()
        # también podrían existir despachadas: si no tienes función, ignora
        for f in fact_pend:
            if f.get("numero_orden") == numero_orden:
                ya_facturada = True
                break
    except:
        pass

    if ya_facturada:
        st.warning("⚠️ Esta orden ya tiene una factura emitida (o está registrada como facturada).")
    else:
        if st.button("✅ Emitir factura", type="primary", use_container_width=True):
            ok, msg, fac = oc.crear_factura_para_orden(numero_orden)
            if ok:
                st.success(f"{msg} — Factura: **{fac}**")
                st.rerun()
            else:
                st.error(msg)

    st.markdown("---")

    # 4) Historial (mínimo): facturas pendientes de envío
    st.subheader("📚 Facturas emitidas (pendientes de envío)")
    facturas = oc.listar_facturas_pendientes_envio()
    if not facturas:
        st.info("No hay facturas pendientes.")
    else:
        df2 = pd.DataFrame([{
            "Factura": f["numero_factura"],
            "Orden": f["numero_orden"],
            "Subtotal": _fm(f["subtotal"]),
            "IVA": _fm(f["iva"]),
            "Total": _fm(f["total"]),
            "Estado": f["estado"],
            "Fecha": f["fecha"],
        } for f in facturas])
        st.dataframe(df2, use_container_width=True, hide_index=True)
