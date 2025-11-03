import streamlit as st
from typing import List, Dict, Any

# Import robusto: primero absoluto; si falla, relativo
try:
    import orden_compra as oc
except ImportError:
    from . import orden_compra as oc


# -------------------------------------------------------
# 🔁 Botón global para volver al menú principal
# -------------------------------------------------------
def boton_volver():
    st.markdown("---")
    if st.button("🏠 Volver al Menú Principal"):
        st.session_state["vista_actual"] = "Home"
        st.rerun()


# -------------------------------------------------------
# 🏠 PÁGINA HOME
# -------------------------------------------------------
def home():
    st.header("🏠 Inicio — Ferretería")
    st.write("Bienvenido al sistema de gestión de **Órdenes de Compra**.")
    st.info("Usa el menú lateral para navegar por las secciones.")


# -------------------------------------------------------
# 🧾 REGISTRAR ORDEN DE COMPRA
# -------------------------------------------------------
def registrar_orden():
    st.header("🧾 Registrar Orden de Compra")

    # Generar automáticamente el número de orden
    numero_orden = oc.generar_numero_orden()
    st.text_input("Número de orden", value=numero_orden, disabled=True)

    with st.form("form_orden"):
        st.subheader("Datos del Cliente")
        col1, col2 = st.columns(2)
        with col1:
            cliente = st.text_input(
                "Cliente", placeholder="Ferretería Don Pepe")
            telefono = st.text_input("Teléfono", placeholder="+56 9 1234 5678")
            comuna = st.text_input("Comuna", placeholder="Santiago")
        with col2:
            direccion = st.text_input(
                "Dirección", placeholder="Av. Siempre Viva 123")
            region = st.text_input("Región", placeholder="RM")

        st.subheader("Productos")
        default_rows = st.session_state.get("num_items", 1)
        num_items = st.number_input(
            "Cantidad de filas de productos",
            min_value=1, max_value=20, value=default_rows, step=1
        )
        st.session_state["num_items"] = num_items

        items: List[Dict[str, Any]] = []
        for i in range(int(num_items)):
            st.markdown(f"**Ítem {i+1}**")
            c1, c2, c3 = st.columns((2, 1, 1))
            with c1:
                prod = st.text_input(
                    f"Producto #{i+1}", key=f"prod_{i}", placeholder="Martillo carpintero")
            with c2:
                precio = st.number_input(
                    f"Precio #{i+1}", key=f"precio_{i}", min_value=0.0, value=0.0, step=100.0)
            with c3:
                cant = st.number_input(
                    f"Cantidad #{i+1}", key=f"cant_{i}", min_value=1, value=1, step=1)
            if prod:
                items.append(
                    {"producto": prod, "precio": precio, "cantidad": cant})

        enviado = st.form_submit_button("Guardar Orden")
        if enviado:
            if (
                not cliente
                or not direccion
                or not telefono
                or not comuna
                or not region
                or not items
            ):
                st.error("Completa todos los campos y al menos un producto.")
            else:
                ok, msg = oc.agregar_orden(
                    cliente, direccion, telefono, comuna, region, items)
                if ok:
                    st.success(msg)
                    st.session_state["num_items"] = 1
                else:
                    st.error(msg)

    boton_volver()


# -------------------------------------------------------
# 📚 LISTAR ÓRDENES DE COMPRA
# -------------------------------------------------------
def listar_ordenes():
    st.header("📚 Órdenes de Compra")
    data = oc.listar_ordenes(limit=200)
    if not data:
        st.info("No hay órdenes registradas todavía.")
        boton_volver()
        return

    rows = []
    for d in data:
        items_txt = "; ".join([
            f"{it['producto']} x{int(it['cantidad'])} (${it['precio']:.0f})"
            for it in d["items"]
        ])
        rows.append([
            d["numero_orden"], d["cliente"], d["comuna"], d["region"],
            items_txt, f"${d['total']:.0f}", d["creado_en"]
        ])

    st.dataframe(rows, use_container_width=True, hide_index=True)
    boton_volver()
