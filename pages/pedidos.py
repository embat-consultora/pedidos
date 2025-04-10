from navigation import make_sidebar
import streamlit as st
from page_utils import apply_page_config
from sheet_connection import get_google_sheet, update_google_sheet,create_gsheets_connection
import pandas as pd
from datetime import datetime
from variables import connectionGeneral, pedidosSheet, pedidosNombre, detalleNombre

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

conn = create_gsheets_connection(connectionGeneral)
# Estilos CSS
with open("style.css") as f:
    st.markdown(f"<style>{f.read()}</style>", unsafe_allow_html=True)

st.title("📋 Pedidos - Clínica Veterinaria")

filtros ,refresh= st.columns([3, 1])
if "df_pedidos" not in st.session_state:
    df_pedidos = get_google_sheet(connectionGeneral, pedidosSheet)
    st.session_state["df_pedidos"] = df_pedidos.copy() if df_pedidos is not None else pd.DataFrame()
if "df_detalle" not in st.session_state:
    df_detalle = conn.read(worksheet=detalleNombre)
    st.session_state["df_detalle"] = df_detalle.copy() if df_detalle is not None else pd.DataFrame()
with refresh:
    if st.button("🔄 Refrescar Pedidos"):
        df_pedidos = get_google_sheet(connectionGeneral, pedidosSheet)
        df_detalle = conn.read(worksheet=detalleNombre)

        if df_pedidos is not None and not df_pedidos.empty:
            st.session_state["df_pedidos"] = df_pedidos.copy()
        if df_detalle is not None and not df_detalle.empty:
            st.session_state["df_detalle"] = df_detalle.copy()
        st.success("✅ Actualizacion correcta")
        st.rerun()

df = st.session_state["df_pedidos"]
detalle = st.session_state["df_detalle"]
if not df.empty:
    df = df.dropna(how='all')
    df["Fecha"] = pd.to_datetime(df["Fecha"], format="%d/%m/%Y", errors="coerce")
    df["Fecha"] = df["Fecha"].dt.strftime("%d/%m/%Y")

    # Agrupar detalle por pedido
    if not detalle.empty:
        detalle_grouped = detalle.groupby("Nro Pedido").apply(
            lambda x: ", ".join(f"{row['Producto']} x{row['Cantidad']}" for _, row in x.iterrows())
        ).reset_index(name="Detalle Pedido")

        # Unir con pedidos
        df = df.merge(detalle_grouped, on="Nro Pedido", how="left")
    else:
        df["Detalle Pedido"] = "Sin detalles"

    # Filtros
    with filtros: 
        filtro = st.radio(
            "📌 Filtrar pedidos por:",
            ("Todos", "Solo urgentes", "Solo de hoy", "Urgentes de hoy","Listos de hoy"),
            horizontal=True
        )

    hoy_str = datetime.now().strftime("%d/%m/%Y")

    # Aplicar filtros según selección
    if filtro == "Solo urgentes":
        df = df[df["Urgente"] == 1]
        df = df[df["Estado"] == "Abierto"]
    elif filtro == "Solo de hoy":
        df = df[df["Fecha"] == hoy_str]
        df = df[df["Estado"] == "Abierto"]
    elif filtro == "Urgentes de hoy":
        df = df[(df["Urgente"] == 1) & (df["Fecha"] == hoy_str)]
        df = df[df["Estado"] == "Abierto"]
    elif filtro == "Listos de hoy":
        df = df[(df["Estado"] == "Listo") & (df["Fecha"] == hoy_str)]
    else:
        df = df[df["Estado"] == "Abierto"]
    


    if df.empty:
        st.warning("⚠️ No hay pedidos que coincidan con los filtros seleccionados.")
    else:
        st.subheader("📦 Pedidos encontrados")
        for index, row in df.iterrows():
            with st.expander(f"Pedido #{row['Nro Pedido']} - {row['Cliente']}"):
                st.write(f"📅 Fecha: {row['Fecha']}")
                st.write(f"📝 Productos: {row['Detalle Pedido']}")
                st.write(f"📍 Dirección: {row['Direccion']}")
                st.write(f"📞 Teléfono: {str(int(float(row['Telefono'])))}")
                st.write(f"🚨 Urgente: {'Sí' if row['Urgente'] == 1 else 'No'}")
                st.write(f"📌 Estado: {row['Estado']}")

                if row['Estado'] == "Abierto":
                    if st.button(f"✅ Marcar como Listo (Pedido #{row['Nro Pedido']})", key=f"boton_{index}"):
                        full_df = st.session_state["df_pedidos"]
                        pedido_idx = full_df.index[full_df["Nro Pedido"] == row["Nro Pedido"]].tolist()
                        if pedido_idx:
                            full_df.at[pedido_idx[0], "Estado"] = "Listo"
                            update_google_sheet(connectionGeneral, pedidosSheet, pedidosNombre, full_df)
                            st.success(f"Pedido #{row['Nro Pedido']} marcado como Listo ✅")
                            st.session_state["df_pedidos"] = full_df.copy()
                            st.rerun()
                        else:
                            st.error("No se pudo encontrar el pedido en el DataFrame completo.")
else:
    st.info("Aquí encontrarás tus pedidos. Todavía no tienes pedidos cargados.")
