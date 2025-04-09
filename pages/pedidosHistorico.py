from navigation import make_sidebar
import streamlit as st
from page_utils import apply_page_config
from sheet_connection import get_google_sheet, update_google_sheet
import pandas as pd
from datetime import datetime
from variables import connectionGeneral, pedidosSheet, pedidosNombre

# Configuración inicial
apply_page_config()

if "logged_in" not in st.session_state or not st.session_state.logged_in:
    st.warning("Sesión expirada. Redirigiendo a login...")
    st.session_state.logged_in = False 
    st.session_state.redirected = True 
    st.switch_page("streamlit_app.py")
else:
    if st.session_state.role == 'admin':
        make_sidebar()

# Estilos CSS
with open("style.css") as f:
    st.markdown(f"<style>{f.read()}</style>", unsafe_allow_html=True)

# Título y botón de refrescar
st.title("📋 Pedidos - Histórico")

if st.button("🔄 Refrescar Pedidos"):
    df_actualizado = get_google_sheet(connectionGeneral, pedidosSheet)
    if df_actualizado is not None and not df_actualizado.empty:
        st.session_state["df_pedidos"] = df_actualizado.copy()
        st.success("✅ Pedidos actualizados desde Google Sheets")

# Si no hay datos guardados, cargarlos por primera vez
if "df_pedidos" not in st.session_state:
    df_inicial = get_google_sheet(connectionGeneral, pedidosSheet)
    if df_inicial is not None and not df_inicial.empty:
        st.session_state["df_pedidos"] = df_inicial.copy()
    else:
        st.info("No hay pedidos para mostrar.")
        st.session_state["df_pedidos"] = pd.DataFrame()

# Usar el DataFrame desde sesión
df = st.session_state["df_pedidos"]

# Validamos que haya datos antes de procesar
if not df.empty:
    df = df.dropna(how='all')
    df["Fecha"] = pd.to_datetime(df["Fecha"], format="%d/%m/%Y", errors="coerce")
    df["Fecha"] = df["Fecha"].dt.strftime("%d/%m/%Y")
    st.dataframe(df)
else:
    st.info("No hay pedidos para mostrar.")