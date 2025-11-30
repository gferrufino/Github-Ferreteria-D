import streamlit as st
import pandas as pd
import login as auth
import menu
import orden_compra as oc

# Inicializa DB / schema y usuario admin
auth.create_tables()

st.set_page_config(
    page_title="Ferretería — Órdenes de Compra",
    page_icon="🛠️",
    layout="wide"
)

# Estado de sesión
for k, v in [
    ("auth_ok", False),
    ("user_id", None),
    ("username", None),
    ("nombre", None),
    ("role", None)
]:
    if k not in st.session_state:
        st.session_state[k] = v


# =======================================================
# LOGIN + REGISTRO
# =======================================================

def login_view():
    st.title("🔐 Login — Ferretería")
    tab_login, tab_register = st.tabs(["Ingresar", "Registrarme"])

    # ----- LOGIN -----
    with tab_login:
        username = st.text_input("Usuario", key="login_user")
        password = st.text_input("Contraseña", type="password", key="login_pass")

        if st.button("Ingresar", type="primary", use_container_width=True):
            user = auth.verify_login(username, password)
            if user:
                st.session_state["auth_ok"] = True
                st.session_state["user_id"] = user["id"]
                st.session_state["username"] = user["username"]
                st.session_state["nombre"] = user.get("nombre")
                st.session_state["role"] = user["role"]
                st.success("Acceso concedido")
                st.rerun()
            else:
                st.error("Usuario o contraseña incorrectos")

    # ----- REGISTRO -----
    with tab_register:
        st.subheader("Crear cuenta")
        r_user = st.text_input("Usuario nuevo", key="r_user")
        r_name = st.text_input("Nombre completo", key="r_name")
        r_pass1 = st.text_input("Contraseña", type="password", key="r_pass1")
        r_pass2 = st.text_input("Repetir contraseña", type="password", key="r_pass2")

        if st.button("Registrarme", type="secondary"):
            if not r_user or not r_pass1:
                st.error("Usuario y contraseña son obligatorios.")
            elif r_pass1 != r_pass2:
                st.error("Las contraseñas no coinciden.")
            else:
                ok, msg = auth.register_user(r_user, r_pass1, r_name)
                if ok:
                    st.success("Cuenta creada. Ingresa con tu usuario y contraseña.")
                else:
                    st.error(msg)


def logout():
    for k in ["auth_ok", "user_id", "username", "nombre", "role"]:
        if k in st.session_state:
            del st.session_state[k]
    st.success("Sesión cerrada")
    st.rerun()


# =======================================================
# ADMINISTRAR USUARIOS
# =======================================================
def admin_users_view():
    st.header("👥 Usuarios registrados")
    users = auth.list_users()
    df = pd.DataFrame(users, columns=["id", "username", "nombre", "role"])
    st.dataframe(df, use_container_width=True, hide_index=True)

    st.markdown("---")
    st.subheader("✏️ Editar usuario")

    if not users:
        st.info("No hay usuarios registrados.")
        return

    options = {f"{u['username']} (id {u['id']})": u["id"] for u in users}
    sel_label = st.selectbox("Selecciona un usuario", list(options.keys()))
    sel_user_id = options[sel_label]

    current = auth.get_user_by_id(sel_user_id) or {}
    c1, c2, c3 = st.columns([1.2, 1.2, 0.8])
    with c1:
        e_username = st.text_input("Usuario", value=current.get("username", ""))
    with c2:
        e_nombre = st.text_input("Nombre", value=current.get("nombre", "") or "")
    with c3:
        e_role = st.selectbox("Rol", ["user", "admin"], index=0 if current.get("role") != "admin" else 1)

    col_save, col_reset = st.columns([1, 1])

    with col_save:
        if st.button("💾 Guardar cambios", type="primary", use_container_width=True):
            ok, msg = auth.update_user(sel_user_id, e_username.strip(), e_nombre.strip() or None, e_role)
            if ok:
                st.success(msg)
                st.rerun()
            else:
                st.error(msg)

    with col_reset:
        with st.expander("🔐 Cambiar contraseña"):
            new_pass1 = st.text_input("Nueva contraseña", type="password", key="np1")
            new_pass2 = st.text_input("Repetir contraseña", type="password", key="np2")
            if st.button("Actualizar contraseña", type="secondary"):
                if not new_pass1:
                    st.error("La contraseña no puede estar vacía.")
                elif new_pass1 != new_pass2:
                    st.error("Las contraseñas no coinciden.")
                else:
                    ok, msg = auth.reset_password(sel_user_id, new_pass1)
                    if ok:
                        st.success(msg)
                    else:
                        st.error(msg)


# =======================================================
# NUEVAS VISTAS (RF4 y RF5)
# =======================================================

def emitir_factura_view():
    st.header("🧾 Emitir Factura")

    ordenes = oc.listar_ordenes(limit=200, user_id=st.session_state.get("user_id"))

    # Solo mostrar órdenes con boleta
    opciones = {
        f"{o['numero_orden']} — {o['cliente']} — {o['creado_en']}":
        o["numero_orden"]
        for o in ordenes
        if oc.obtener_boleta_por_orden(o["numero_orden"])
    }

    if not opciones:
        st.info("No hay órdenes con boleta disponible para facturar.")
        return

    sel = st.selectbox("Selecciona una orden", list(opciones.keys()))
    numero_orden = opciones[sel]

    if st.button("Emitir Factura", type="primary"):
        ok, msg, fac = oc.crear_factura_para_orden(numero_orden)
        if ok:
            st.success(f"{msg} — Factura generada: {fac}")
        else:
            st.error(msg)


def enviar_productos_view():
    st.header("📦 Enviar Productos")

    facturas = oc.listar_facturas_pendientes_envio()

    if not facturas:
        st.info("No hay facturas pendientes de envío.")
        return

    opciones = {
        f"{f['numero_factura']} — Orden {f['numero_orden']} — Total ${f['total']}": f["numero_factura"]
        for f in facturas
    }

    sel = st.selectbox("Selecciona una factura", list(opciones.keys()))
    numero_factura = opciones[sel]

    if st.button("Marcar como despachado", type="primary"):
        ok, msg = oc.registrar_envio(numero_factura)
        if ok:
            st.success(msg)
        else:
            st.error("Error registrando el envío.")
def mostrar_factura_view(factura):
    st.markdown("## 📄 Factura emitida")
    st.write(f"**Factura:** {factura['numero_factura']} — **Orden:** {factura['numero_orden']}")
    st.write(f"**Fecha:** {factura['fecha']}")
    st.write("---")

    st.write(f"**Cliente:** {factura['cliente']}")
    st.write(f"**Dirección:** {factura['direccion']}, {factura['comuna']}, {factura['region']}")
    st.write(f"**Teléfono:** {factura['telefono']}")
    st.write("---")

    st.markdown("### 🛒 Ítems")
    for it in factura["items"]:
        st.write(f"- {it['producto']} — {it['cantidad']} x ${it['precio']:,}".replace(",", "."))

    st.write("---")
    st.write(f"**Subtotal:** ${int(factura['subtotal']):,}".replace(",", "."))
    st.write(f"**IVA (19%):** ${int(factura['iva']):,}".replace(",", "."))
    st.write(f"**Total:** ${int(factura['total']):,}".replace(",", "."))
    st.write("---")


# =======================================================
# USUARIO NORMAL — Mis órdenes
# =======================================================
def my_orders_view():
    st.header("🧾 Mis Órdenes")
    uid = st.session_state.get("user_id")
    data = oc.listar_ordenes(limit=200, user_id=uid)
    if not data:
        st.info("Aún no tienes órdenes registradas.")
        return
    rows = []
    for d in data:
        rows.append({
            "N° Orden": d["numero_orden"],
            "Cliente": d["cliente"],
            "Total": d["total"],
            "Fecha": d["creado_en"],
        })
    st.dataframe(pd.DataFrame(rows), use_container_width=True, hide_index=True)


# =======================================================
# MAIN VIEW
# =======================================================
def main_view():
    st.sidebar.title("Menú")
    is_admin = st.session_state.get("role") == "admin"

    req = st.session_state.pop("request_nav", None)
    if req:
        st.session_state["nav_choice"] = req

    if is_admin:
        options = ["Home", "Usuarios registrados", "Cerrar sesión"]
    else:
        options = [
            "Home",
            "Registrar Orden",
            "Mis Órdenes",
            "Emitir Factura",
            "Enviar Productos",
            "Cerrar sesión"
        ]

    if "nav_choice" not in st.session_state:
        st.session_state["nav_choice"] = "Home"

    choice = st.sidebar.radio("Navegación", options, key="nav_choice")

    st.sidebar.divider()
    st.sidebar.caption(
        f"Conectado como: **{st.session_state.get('username', '')}** "
        f"({st.session_state.get('role', '')})"
    )

    # Routing de vistas
    if choice == "Home":
        menu.home()
    elif choice == "Registrar Orden":
        menu.registrar_orden()
    elif choice == "Mis Órdenes":
        menu.listar_ordenes(user_id=st.session_state.get("user_id"))
    elif choice == "Emitir Factura":
        emitir_factura_view()
    elif choice == "Enviar Productos":
        enviar_productos_view()
    elif choice == "Usuarios registrados":
        admin_users_view()
    elif choice == "Cerrar sesión":
        logout()


# =======================================================
# APP START
# =======================================================
if st.session_state["auth_ok"]:
    main_view()
else:
    login_view()
