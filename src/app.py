import streamlit as st
import pandas as pd
import login as auth
import menu
import orden_compra as oc

# Inicializa DB / schema y usuario admin
auth.create_tables()

st.set_page_config(page_title="Ferretería — Órdenes de Compra",
                   page_icon="🛠️", layout="wide")

# Estado de sesión
for k, v in [("auth_ok", False), ("user_id", None), ("username", None), ("nombre", None), ("role", None)]:
    if k not in st.session_state:
        st.session_state[k] = v

# -------------------------------
# Vistas auxiliares
# -------------------------------


def login_view():
    st.title("🔐 Login — Ferretería")
    tab_login, tab_register = st.tabs(["Ingresar", "Registrarme"])

    with tab_login:
        username = st.text_input("Usuario", key="login_user")
        password = st.text_input(
            "Contraseña", type="password", key="login_pass")
        col1, col2 = st.columns([1, 1])
        with col1:
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
        with col2:
            st.caption("")

    with tab_register:
        st.subheader("Crear cuenta")
        r_user = st.text_input("Usuario nuevo", key="r_user")
        r_name = st.text_input("Nombre completo", key="r_name")
        r_pass1 = st.text_input("Contraseña", type="password", key="r_pass1")
        r_pass2 = st.text_input("Repetir contraseña",
                                type="password", key="r_pass2")
        if st.button("Registrarme", type="secondary"):
            if not r_user or not r_pass1:
                st.error("Usuario y contraseña son obligatorios.")
            elif r_pass1 != r_pass2:
                st.error("Las contraseñas no coinciden.")
            else:
                ok, msg = auth.register_user(r_user, r_pass1, r_name)
                if ok:
                    st.success(
                        "Cuenta creada. Ingresa con tu usuario y contraseña.")
                else:
                    st.error(msg)


def logout():
    for k in ["auth_ok", "user_id", "username", "nombre", "role"]:
        if k in st.session_state:
            del st.session_state[k]
    st.success("Sesión cerrada")
    st.rerun()

# -------------------------------
# Vista de administración: lista + edición + reset de clave
# -------------------------------


def admin_users_view():
    st.header("👥 Usuarios registrados")

    # Tabla de usuarios
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
        e_username = st.text_input(
            "Usuario", value=current.get("username", ""))
    with c2:
        e_nombre = st.text_input(
            "Nombre", value=current.get("nombre", "") or "")
    with c3:
        e_role = st.selectbox(
            "Rol", ["user", "admin"], index=0 if current.get("role") != "admin" else 1)

    col_save, col_reset = st.columns([1, 1])

    with col_save:
        if st.button("💾 Guardar cambios", type="primary", use_container_width=True):
            ok, msg = auth.update_user(
                sel_user_id, e_username.strip(), e_nombre.strip() or None, e_role)
            if ok:
                st.success(msg)
                st.rerun()
            else:
                st.error(msg)

    with col_reset:
        with st.expander("🔐 Cambiar contraseña"):
            new_pass1 = st.text_input(
                "Nueva contraseña", type="password", key="np1")
            new_pass2 = st.text_input(
                "Repetir contraseña", type="password", key="np2")
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

    st.markdown("---")
    st.subheader("➕ Crear usuario")
    c1, c2, c3, c4 = st.columns([1.2, 1.2, 1.2, 0.8])
    with c1:
        u_user = st.text_input("Usuario", key="au_user")
    with c2:
        u_name = st.text_input("Nombre", key="au_name")
    with c3:
        u_pass = st.text_input("Contraseña", type="password", key="au_pass")
    with c4:
        role = st.selectbox("Rol", ["user", "admin"], index=0, key="au_role")
    if st.button("Crear", type="primary"):
        ok, msg = auth.create_user_admin(u_user, u_pass, u_name, role=role)
        if ok:
            st.success(msg)
            st.rerun()
        else:
            st.error(msg)

# -------------------------------
# Usuario normal
# -------------------------------


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

# -------------------------------
# Main
# -------------------------------


def main_view():
    st.sidebar.title("Menú")
    is_admin = st.session_state.get("role") == "admin"

    # --- procesa solicitudes de navegación ANTES de instanciar el radio ---
    req = st.session_state.pop("request_nav", None)
    if req:
        st.session_state["nav_choice"] = req

    # items del menú
    admin_items = ["Home", "Usuarios registrados", "Cerrar sesión"]
    user_items = ["Home", "Registrar Orden", "Mis Órdenes", "Cerrar sesión"]
    options = admin_items if is_admin else user_items

    # valor por defecto del radio
    if "nav_choice" not in st.session_state:
        st.session_state["nav_choice"] = "Home"

    # crea el radio con key fija
    choice = st.sidebar.radio("Navegación", options, key="nav_choice")

    st.sidebar.divider()
    st.sidebar.caption(
        f"Conectado como: **{st.session_state.get('username', '')}** "
        f"({st.session_state.get('role', '')})"
    )

    if choice == "Home":
        menu.home()
    elif choice == "Registrar Orden":
        menu.registrar_orden()
    elif choice == "Mis Órdenes":
        menu.listar_ordenes(user_id=st.session_state.get("user_id"))
    elif choice == "Usuarios registrados":
        admin_users_view()
    elif choice == "Cerrar sesión":
        logout()


if st.session_state["auth_ok"]:
    main_view()
else:
    login_view()
