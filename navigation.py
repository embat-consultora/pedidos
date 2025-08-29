import streamlit as st
from time import sleep
from variables import logoutButton
from page_utils import flag_activo
def get_current_page_name():
    return st.session_state.get("current_page", "")


def make_sidebar():
    with st.sidebar:
        st.markdown(
        """
        <style>
        [data-testid="stSidebar"] {
            width: 200px;  /* Adjust the width to your preference */
        }
        </style>
        """,
        unsafe_allow_html=True
    )
        st.title("Menu")
        st.write("")
        st.write("")

        if st.session_state.get("logged_in", False):
            st.page_link("pages/pedidos.py", label="Pedidos")
            if flag_activo("stock"):
                st.page_link("pages/productos.py", label="Productos")
                st.page_link("pages/productos_qr.py", label="Productos QR")
            if flag_activo("historico"):
                st.page_link("pages/pedidosHistorico.py", label="Historico")
            st.write("")
            st.write("")

            if st.button(logoutButton):
                logout()

        elif get_current_page_name() != "streamlit_app":
            # If anyone tries to access a secret page without being logged in,
            # redirect them to the login page
            st.switch_page("streamlit_app.py")

def logout():
    for key in list(st.session_state.keys()):
        del st.session_state[key]
    sleep(0.5)
    st.rerun()

