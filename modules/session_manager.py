import streamlit as st
from modules.data_base import getEqual

# Función para redirigir según el rol del usuario
def redirect_by_role():
    rutas = {
        "admin": "pages/dashboard_admin.py",
        "psicologo": "pages/dashboard_psicologos.py",
        "pm": "pages/pm_usuarios.py",
        "consultora": "pages/consultora_calendar.py"
    }
    rol = st.session_state.get("role")
    if rol in rutas:
        st.switch_page(rutas[rol])
    else:
        st.error("Rol no reconocido.")

# Cargar datos del usuario desde Supabase y guardar en session_state
def load_user(email):
    response = getEqual("users", "email", email)
    if response:
        user = response[0]
        st.session_state.username = user["email"]
        st.session_state.logged_in = True
        return True
    return False

def is_authenticated():
    return (
        st.session_state.get("logged_in") or
        (hasattr(st, "experimental_user") and st.experimental_user and st.experimental_user.is_logged_in)
    )

def validate_get_user():
    if hasattr(st, "experimental_user") and st.experimental_user and st.experimental_user.is_logged_in:
        if "role" not in st.session_state:
            email = st.email
            if load_user(email):
                print('user loaded correctly')
                return True
            else:
                st.error("Tu cuenta de Google no está autorizada.")
                st.stop()

# Verificación inicial en cualquier página protegida
def is_logged():
    if not is_authenticated():
        st.warning("Redirigiendo al inicio de sesión...")
        st.session_state.logged_in = False
        st.session_state.redirected = True
        st.switch_page("app.py")
