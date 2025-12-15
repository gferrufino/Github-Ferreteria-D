import streamlit as st
import pandas as pd
import orden_compra as oc

ESTADOS = ["en_preparacion", "despachado", "entregado", "no_entregado"]

def enviar_productos_view():
    st.header("📦 Gestión de Envíos")

    # ---- KPIs ----
    facturas_pend = oc.listar_facturas_pendientes_envio()  # estado='facturada'
    envios = oc.listar_envios(limit=500)

    total_pend = len(facturas_pend)
    total_envios = len(envios)
    total_desp = sum(1 for e in envios if e.get("estado_envio") == "despachado")
    total_ent = sum(1 for e in envios if e.get("estado_envio") == "entregado")
    total_noent = sum(1 for e in envios if e.get("estado_envio") == "no_entregado")

    c1, c2, c3, c4 = st.columns(4)
    c1.metric("Pendientes de envío", total_pend)
    c2.metric("Despachados", total_desp)
    c3.metric("Entregados", total_ent)
    c4.metric("No entregados", total_noent)

    st.markdown("---")

    # ---- Bloque 1: Crear envío desde factura facturada ----
    st.subheader("🧾 Facturas con Productos por despachar")

    if not facturas_pend:
        st.info("No hay facturas pendientes de envío (estado: facturada).")
    else:
        opciones = {
            f"{f['numero_factura']} — OC {f['numero_orden']} — Total ${int(f['total']):,}".replace(",", "."): f["numero_factura"]
            for f in facturas_pend
        }
        sel = st.selectbox("Selecciona una factura", list(opciones.keys()))
        numero_factura = opciones[sel]

        colA, colB = st.columns([1, 1])
        with colA:
            estado_inicial = st.selectbox("Estado inicial", ["despachado", "en_preparacion"], index=0)
        with colB:
            st.caption("Tip: 'en_preparacion' sirve cuando ya está armada pero aún no sale a despacho.")

        if st.button("✅ Registrar envío / actualizar estado", type="primary"):
            ok, msg = oc.registrar_envio(numero_factura, estado_envio=estado_inicial)
            if ok:
                st.success(msg)
                st.rerun()
            else:
                st.error(msg)

    st.markdown("---")

    # ---- Bloque 2: Tabla de envíos con filtros y cambios de estado ----
    st.subheader("📋 Historial y estados de envíos")

    if not envios:
        st.info("Aún no hay envíos registrados.")
        return

    # Filtro
    filtro = st.multiselect("Filtrar por estado", ESTADOS, default=ESTADOS)

    rows = [e for e in envios if e.get("estado_envio") in filtro]

    df = pd.DataFrame(rows)
    # Orden de columnas si existen
    cols = [c for c in ["id", "numero_factura", "numero_orden", "fecha_envio", "estado_envio"] if c in df.columns]
    df = df[cols]

    st.dataframe(df, use_container_width=True, hide_index=True)

    st.markdown("### 🔄 Cambiar estado de un envío")
    opciones_envio = {f"ID {r['id']} — {r.get('numero_factura','')} — {r.get('estado_envio','')}": r["id"] for r in rows}

    sel_envio = st.selectbox("Selecciona un envío", list(opciones_envio.keys()))
    envio_id = opciones_envio[sel_envio]
    nuevo_estado = st.selectbox("Nuevo estado", ESTADOS, index=0)

    if st.button("Guardar cambio de estado"):
        ok, msg = oc.actualizar_estado_envio(envio_id, nuevo_estado)
        if ok:
            st.success(msg)
            st.rerun()
        else:
            st.error(msg)
