from __future__ import annotations
import re
from typing import List, Dict, Any
import streamlit as st

# Import robusto: primero absoluto; si falla, relativo
try:
    import orden_compra as oc  # si ejecutas: streamlit run src/app.py
except ImportError:
    from . import orden_compra as oc  # si estás en paquete

# Estado inicial
if "vista_actual" not in st.session_state:
    st.session_state["vista_actual"] = "Home"
if "num_items" not in st.session_state:
    st.session_state["num_items"] = 1


def _formatea_miles(x: float | int) -> str:
    try:
        return f"${int(round(float(x))):,}".replace(",", ".")
    except Exception:
        return str(x)


def _telefono_valido(telefono: str) -> bool:
    tel = telefono.replace(" ", "")
    return bool(re.fullmatch(r"^\+?56?9?\d{8}$", tel))


def boton_volver():
    st.markdown("---")
    if st.button("🏠 Volver al Menú Principal", use_container_width=True):
        # marcamos una navegación solicitada y forzamos un rerun
        st.session_state["request_nav"] = "Home"
        st.rerun()


def home():
    st.header("🏠 Inicio — Ferretería-D")
    st.write("Bienvenido al sistema de gestión de **Órdenes de Compra**.")
    st.info("Usa el menú lateral para navegar por las secciones.")


def registrar_orden():
    st.header("🧾 Registrar Orden de Compra")

    # Estado para ítems dinámicos y número de orden visible
    if "items_dyn" not in st.session_state:
        st.session_state["items_dyn"] = [
            {"producto": "", "precio": 0.0, "cantidad": 1}]
    if "numero_orden_ui" not in st.session_state:
        try:
            st.session_state["numero_orden_ui"] = oc.generar_numero_orden()
        except Exception as e:
            st.error(f"No fue posible generar número de orden: {e}")
            boton_volver()
            return

    st.text_input("Número de orden",
                  value=st.session_state["numero_orden_ui"], disabled=True, key="numero_orden_ro")

    with st.form("form_orden", clear_on_submit=False):
        st.subheader("Datos del Cliente")
        col1, col2 = st.columns(2)
        with col1:
            cliente = st.text_input(
                "Cliente", placeholder="Ferretería Don Pepe", key="f_cliente").strip()
            telefono = st.text_input(
                "Teléfono", placeholder="+56 9 1234 5678", key="f_telefono").strip()
            comuna = st.text_input(
                "Comuna", placeholder="Santiago", key="f_comuna").strip()
        with col2:
            direccion = st.text_input(
                "Dirección", placeholder="Av. Siempre Viva 123", key="f_direccion").strip()
            region = st.text_input(
                "Región", placeholder="RM", key="f_region").strip()

        st.subheader("Productos")

        # Render dinámico de filas
        items = []
        total_items = 0
        total_monto = 0.0

        for i in range(len(st.session_state["items_dyn"])):
            it = st.session_state["items_dyn"][i]
            st.markdown(f"**Ítem {i+1}**")
            c1, c2, c3, c4 = st.columns((2, 1, 1, 0.5))
            with c1:
                prod = st.text_input(f"Producto #{i+1}", key=f"prod_{i}", value=it.get(
                    "producto", ""), placeholder="Martillo carpintero").strip()
            with c2:
                precio = st.number_input(
                    f"Precio #{i+1}", key=f"precio_{i}", min_value=0.0, value=float(it.get("precio", 0.0)), step=100.0)
            with c3:
                cant = st.number_input(
                    f"Cantidad #{i+1}", key=f"cant_{i}", min_value=1, value=int(it.get("cantidad", 1)), step=1)
            with c4:
                borrar = st.checkbox(
                    "🗑️", key=f"del_{i}", help="Eliminar este ítem")

            st.session_state["items_dyn"][i] = {
                "producto": prod, "precio": float(precio), "cantidad": int(cant)}
            if prod:
                items.append({"producto": prod, "precio": float(
                    precio), "cantidad": int(cant)})
                total_items += int(cant)
                total_monto += float(precio) * int(cant)
            if borrar:
                st.session_state["items_dyn"][i]["__delete__"] = True

        # limpia eliminados
        st.session_state["items_dyn"] = [
            x for x in st.session_state["items_dyn"] if not x.get("__delete__")]

        # botones del form
        add_more = st.form_submit_button(
            "➕ Agregar producto", type="secondary")
        guardar = st.form_submit_button("💾 Guardar Orden", type="primary")

        if add_more:
            st.session_state["items_dyn"].append(
                {"producto": "", "precio": 0.0, "cantidad": 1})
            st.rerun()

        st.info(
            f"**Resumen:** {total_items} producto(s) — Total estimado (neto): ${int(total_monto):,}".replace(",", "."))

        # Guardar
        if guardar:
            if not cliente:
                st.error("El **Cliente** es obligatorio.")
            elif not direccion:
                st.error("La **Dirección** es obligatoria.")
            elif not telefono or not _telefono_valido(telefono):
                st.error("El **Teléfono** no parece válido. Ej: +56912345678")
            elif not comuna:
                st.error("La **Comuna** es obligatoria.")
            elif not region:
                st.error("La **Región** es obligatoria.")
            elif not items:
                st.error("Agrega al menos **1** producto.")
            elif any(it["precio"] <= 0 for it in items):
                st.error("Todos los **Precios** deben ser > 0.")
            elif any(it["cantidad"] <= 0 for it in items):
                st.error("Todas las **Cantidades** deben ser > 0.")
            else:
                try:
                    # Guardar OC usando el número mostrado en UI
                    ok, msg, nro = oc.agregar_orden(
                        cliente=cliente, direccion=direccion, telefono=telefono,
                        comuna=comuna, region=region, items=items,
                        user_id=st.session_state.get("user_id"),
                        numero_orden_preasignado=st.session_state["numero_orden_ui"]
                    )
                    if ok:
                        st.success(msg)

                        # ⬇️⬇️⬇️ AQUÍ VA EL BLOQUE DE LA BOLETA (con IVA y detalle) ⬇️⬇️⬇️
                        bok, bmsg, bnum = oc.crear_boleta_para_orden(
                            st.session_state["numero_orden_ui"])
                        if bok:
                            st.success(
                                f"{bmsg} (OC: {st.session_state['numero_orden_ui']})")

                            # Mostrar detalle de boleta con IVA
                            boleta = oc.obtener_boleta_por_numero(bnum)
                            if boleta:
                                st.markdown("### 🧾 Detalle de Boleta")
                                st.write(
                                    f"**Boleta:** {boleta['numero_boleta']} — **Orden:** {boleta['numero_orden']}")
                                st.write(f"**Cliente:** {boleta['cliente']}")
                                st.write(
                                    f"**Dirección:** {boleta['direccion']}, {boleta['comuna']}, {boleta['region']}")
                                st.write(f"**Teléfono:** {boleta['telefono']}")

                                # Detalle de productos
                                lines = []
                                for it in boleta["items"]:
                                    lines.append(
                                        f"- {it['producto']} — {int(it['cantidad'])} x ${int(it['precio']):,}".replace(",", "."))
                                st.markdown("\n".join(lines))

                                # Desglose de totales
                                st.markdown("---")
                                st.write(
                                    f"**Total ítems:** {boleta['total_items']}")
                                st.write(
                                    f"**Neto:** ${int(round(boleta['neto'])):,}".replace(",", "."))
                                st.write(
                                    f"**IVA (19%):** ${int(round(boleta['iva'])):,}".replace(",", "."))
                                st.write(
                                    f"**Total a pagar:** ${int(round(boleta['total'])):,}".replace(",", "."))
                        else:
                            st.warning(f"No se pudo emitir boleta: {bmsg}")
                        # ⬆️⬆️⬆️ FIN DEL BLOQUE DE BOLETA ⬆️⬆️⬆️

                        # reset para nueva OC
                        st.session_state["items_dyn"] = [
                            {"producto": "", "precio": 0.0, "cantidad": 1}]
                        st.session_state["numero_orden_ui"] = oc.generar_numero_orden(
                        )
                    else:
                        st.error(msg)
                except Exception as e:
                    st.error(f"No fue posible guardar la orden: {e}")

    boton_volver()


def listar_ordenes(user_id: int | None = None):
    import pandas as pd

    # Helpers locales por si no existen en tu archivo
    def _fm(n):
        try:
            return f"${int(round(float(n))):,}".replace(",", ".")
        except:
            return str(n)

    titulo = "📚 Órdenes de Compra" if user_id is None else "🧾 Órdenes del usuario"
    st.header(titulo)

    try:
        data = oc.listar_ordenes(limit=200, user_id=user_id)
    except Exception as e:
        st.error(f"No fue posible obtener órdenes: {e}")
        boton_volver()
        return

    if not data:
        st.info(
            "No hay órdenes registradas." if user_id is None else "Este usuario no tiene órdenes.")
        boton_volver()
        return

    # ---------- Tabla de órdenes ----------
    rows: list[dict[str, Any]] = []
    for d in data:
        items_txt = "; ".join(
            f"{it.get('producto', '?')} x{int(it.get('cantidad', 0))} ({_fm(it.get('precio', 0))})"
            for it in d.get("items", [])
        )
        rows.append(
            {
                "N° Orden": d.get("numero_orden"),
                "Cliente": d.get("cliente"),
                "Comuna": d.get("comuna"),
                "Región": d.get("region"),
                "Ítems": items_txt,
                "Total (neto)": _fm(d.get("total", 0)),
                "Creado en": d.get("creado_en"),
            }
        )

    df = pd.DataFrame(rows, columns=[
                      "N° Orden", "Cliente", "Comuna", "Región", "Ítems", "Total (neto)", "Creado en"])
    st.dataframe(df, use_container_width=True, hide_index=True)

    # Descargar CSV
    csv = df.to_csv(index=False).encode("utf-8")
    st.download_button("⬇️ Descargar CSV", data=csv,
                       file_name="ordenes_compra.csv", mime="text/csv")

    st.markdown("---")
    st.subheader("🧾 Boleta asociada")

    # ---------- Selector de orden ----------
    opciones = {
        f"{r['N° Orden']} — {r['Cliente']} — {r['Creado en']}": r["N° Orden"] for r in rows}
    etiqueta = st.selectbox("Selecciona una orden", list(opciones.keys()))
    numero_orden_sel = opciones[etiqueta]

    # Traer boleta existente (sin botón de emitir)
    boleta = oc.obtener_boleta_por_orden(numero_orden_sel)
    if not boleta:
        st.info("Esta orden aún no tiene boleta registrada.")
        boton_volver()
        return

    _render_boleta_detalle(boleta)
    boton_volver()


# ---------- Muestra boleta con detalle + IVA ----------
def _render_boleta_detalle(boleta: Dict[str, Any]):
    def _fm(n):
        try:
            return f"${int(round(float(n))):,}".replace(",", ".")
        except:
            return str(n)

    st.markdown("### 🧾 Detalle de Boleta")
    st.write(
        f"**Boleta:** {boleta['numero_boleta']} — **Orden:** {boleta['numero_orden']}")
    st.write(f"**Cliente:** {boleta['cliente']}")
    st.write(
        f"**Dirección:** {boleta['direccion']}, {boleta['comuna']}, {boleta['region']}")
    st.write(f"**Teléfono:** {boleta['telefono']}")
    st.write(f"**Fecha:** {boleta['creado_en']}")

    # Detalle de productos
    lines = []
    for it in boleta["items"]:
        lines.append(
            f"- {it.get('producto', '?')} — {int(it.get('cantidad', 0))} x {_fm(it.get('precio', 0))}")
    st.markdown("\n".join(lines) if lines else "_(Sin ítems)_")

    # Desglose totales
    st.markdown("---")
    st.write(f"**Total ítems:** {boleta.get('total_items', 0)}")
    st.write(f"**Neto:** {_fm(boleta.get('neto', 0))}")
    st.write(f"**IVA (19%):** {_fm(boleta.get('iva', 0))}")
    st.write(f"**Total a pagar:** {_fm(boleta.get('total', 0))}")

    # 👉 Botón para imprimir la boleta
    try:
        html = oc.boleta_a_html(boleta)
        st.download_button(
            "🖨️ Imprimir / Descargar Boleta",
            data=html.encode("utf-8"),
            file_name=f"{boleta['numero_boleta']}.html",
            mime="text/html",
            help="Descarga un archivo HTML listo para imprimir"
        )
    except Exception as e:
        st.warning(f"No fue posible generar la versión imprimible: {e}")
