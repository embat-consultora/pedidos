from navigation import make_sidebar
import streamlit as st
from page_utils import apply_page_config
from sheet_connection import get_google_sheet,create_gsheets_connection
import pandas as pd
from datetime import datetime
from variables import connectionGeneral, pedidosSheet, detalleNombre

# Configuración inicial
apply_page_config()

conn = create_gsheets_connection(connectionGeneral)
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
    df_pedidos = get_google_sheet(connectionGeneral, pedidosSheet)
    df_detalle = conn.read(worksheet=detalleNombre)

    if df_pedidos is not None and not df_pedidos.empty:
        st.session_state["df_pedidos"] = df_pedidos.copy()
    if df_detalle is not None and not df_detalle.empty:
        st.session_state["df_detalle"] = df_detalle.copy()
    st.success("✅ Actualizacion correcta")
    st.rerun()
    

# Si no hay datos guardados, cargarlos por primera vez
if "df_pedidos" not in st.session_state:
    df_pedidos = get_google_sheet(connectionGeneral, pedidosSheet)
    st.session_state["df_pedidos"] = df_pedidos.copy() if df_pedidos is not None else pd.DataFrame()
if "df_detalle" not in st.session_state:
    df_detalle = conn.read(worksheet=detalleNombre)
    st.session_state["df_detalle"] = df_detalle.copy() if df_detalle is not None else pd.DataFrame()

df = st.session_state["df_pedidos"]
detalle = st.session_state["df_detalle"]
# Validamos que haya datos antes de procesar
if not df.empty:
    df = df.dropna(how='all')
    df["Fecha"] = pd.to_datetime(df["Fecha"], format="%d/%m/%Y", errors="coerce")
    df["Fecha"] = df["Fecha"].dt.strftime("%d/%m/%Y")
    if not detalle.empty:
        detalle_grouped = (
            detalle.groupby("Nro Pedido")[["Producto", "Cantidad"]]
            .apply(lambda x: ", ".join(f"{row['Producto']} x{row['Cantidad']}" for _, row in x.iterrows()))
            .reset_index(name="Detalle Pedido"))
        # Unir con pedidos
        df = df.merge(detalle_grouped, on="Nro Pedido", how="left")
    else:
        df["Detalle Pedido"] = "Sin detalles"
    st.dataframe(df, hide_index=True)
else:
    st.info("No hay pedidos para mostrar.")