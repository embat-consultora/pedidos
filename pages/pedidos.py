from navigation import make_sidebar
import streamlit as st
from page_utils import apply_page_config
from sheet_connection import get_google_sheet, update_google_sheet
import pandas as pd
from datetime import datetime
from variables import connectionGeneral, pedidosSheet, pedidosNombre

# Configuración inicial
st.session_state["current_page"] = "pedidos"
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
st.title("📋 Pedidos - Clínica Veterinaria")

if st.button("🔄 Refrescar Pedidos"):
    df_completo = get_google_sheet(connectionGeneral, pedidosSheet)
    st.session_state["df_pedidos"] = df_completo.copy()
    st.success("✅ Pedidos actualizados desde Google Sheets")

# Si no hay datos guardados, cargarlos por primera vez
if "df_pedidos" not in st.session_state:
    df_completo = get_google_sheet(connectionGeneral, pedidosSheet)
    st.session_state["df_pedidos"] = df_completo.copy() 
else:
    df = st.session_state["df_pedidos"]

df = get_google_sheet(connectionGeneral, pedidosSheet)
# Limpieza y formato
df = df.dropna(how='all')
df["Fecha"] = pd.to_datetime(df["Fecha"], format="%d/%m/%Y", errors="coerce")
df["Fecha"] = df["Fecha"].dt.strftime("%d/%m/%Y")

# Filtros
filtro = st.radio(
    "📌 Filtrar pedidos por:",
    ("Todos", "Solo urgentes", "Solo de hoy", "Urgentes de hoy"),
    horizontal=True
)

if filtro == "Solo urgentes":
    df = df[df["Urgente"] == 1]
elif filtro == "Solo de hoy":
    hoy_str = datetime.now().strftime("%d/%m/%Y")
    df = df[df["Fecha"] == hoy_str]
elif filtro == "Urgentes de hoy":
    hoy_str = datetime.now().strftime("%d/%m/%Y")
    df = df[(df["Urgente"] == 1) & (df["Fecha"] == hoy_str)]

# Mostrar solo pedidos abiertos
df = df[df["Estado"] == "Abierto"]

# Mostrar resultados
if df.empty:
    st.warning("⚠️ No hay pedidos que coincidan con los filtros seleccionados.")
else:
    st.subheader("📦 Pedidos encontrados")
    for index, row in df.iterrows():
        with st.expander(f"Pedido #{row['Nro Pedido']} - {row['Cliente']}"):
            st.write(f"📅 Fecha: {row['Fecha']}")
            st.write(f"📝 Producto: {row['Pedido']}")
            st.write(f"📦 Cantidad: {row['Cantidad']}")
            st.write(f"📍 Dirección: {row['Direccion']}")
            st.write(f"📞 Teléfono: {row['Telefono']}")
            st.write(f"🚨 Urgente: {'Sí' if row['Urgente'] == 1 else 'No'}")
            st.write(f"📌 Estado: {row['Estado']}")

            if row['Estado'] == "Abierto":
                if st.button(f"✅ Marcar como Listo (Pedido #{row['Nro Pedido']})", key=f"boton_{index}"):
                    # Recuperar todo el DataFrame completo
                    full_df = st.session_state["df_pedidos"]

                    # Buscar por Nro Pedido (porque el índice puede haber cambiado por filtros)
                    pedido_idx = full_df.index[full_df["Nro Pedido"] == row["Nro Pedido"]].tolist()
                    if pedido_idx:
                        full_df.at[pedido_idx[0], "Estado"] = "Listo"

                        # Actualizar en Google Sheets
                        update_google_sheet(connectionGeneral, pedidosSheet, pedidosNombre, full_df)

                        st.success(f"Pedido #{row['Nro Pedido']} marcado como Listo ✅")

                        # Refrescar los datos en sesión
                        st.session_state["df_pedidos"] = full_df.copy()
                        st.rerun()
                    else:
                        st.error("No se pudo encontrar el pedido en el DataFrame completo.")

