import streamlit as st
import login as auth
import menu

# Inicializa DB si no existe
auth.create_tables()

st.set_page_config(page_title="Ferretería — Órdenes de Compra",
                   page_icon="🛠️", layout="wide")

if "auth_ok" not in st.session_state:
    st.session_state["auth_ok"] = False
if "username" not in st.session_state:
    st.session_state["username"] = None


def login_view():
    st.title("🔐 Login — Ferretería")
    username = st.text_input("Usuario")
    password = st.text_input("Contraseña", type="password")
    col1, col2 = st.columns([1, 1])
    with col1:
        if st.button("Ingresar", type="primary"):
            if auth.verify_login(username, password):
                st.session_state["auth_ok"] = True
                st.session_state["username"] = username
                st.success("Acceso concedido")
                st.rerun()
            else:
                st.error("Usuario o contraseña incorrectos")
    with col2:
        st.caption("Usuario inicial: **admin** / **admin123**")


def logout():
    for k in ["auth_ok", "username"]:
        if k in st.session_state:
            del st.session_state[k]
    st.success("Sesión cerrada")
    st.rerun()


def main_view():
    st.sidebar.title("Menú")
    choice = st.sidebar.radio(
        "Navegación", ["Home", "Registrar Orden", "Órdenes", "Cerrar sesión"])
    st.sidebar.divider()
    st.sidebar.caption(
        f"Conectado como: **{st.session_state.get('username', '')}**")

    if choice == "Home":
        menu.home()
    elif choice == "Registrar Orden":
        menu.registrar_orden()
    elif choice == "Órdenes":
        menu.listar_ordenes()
    elif choice == "Cerrar sesión":
        logout()


if st.session_state["auth_ok"]:
    main_view()
else:
    login_view()
