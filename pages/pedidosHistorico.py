import streamlit as st
from navigation import make_sidebar
from page_utils import apply_page_config
import pandas as pd
from modules.data_base import get
from variables import pedidoTable, detallePedidoTable, productoTable

# Configuración inicial
st.session_state["current_page"] = "pedidos"
apply_page_config()

if "logged_in" not in st.session_state or not st.session_state.logged_in:
    st.warning("Sesión expirada. Redirigiendo a login...")
    st.session_state.logged_in = False 
    st.session_state.redirected = True 
    st.switch_page("streamlit_app.py")
else:
    make_sidebar()

# Estilos CSS
with open("style.css") as f:
    st.markdown(f"<style>{f.read()}</style>", unsafe_allow_html=True)

st.title("📋 Histórico Pedidos")

filtros, refresh = st.columns([3, 1])

# 🔄 Cargar pedidos y detalles
if "df_pedidos" not in st.session_state:
    df_pedidos = get(pedidoTable)
    st.session_state["df_pedidos"] = pd.DataFrame(df_pedidos) if df_pedidos else pd.DataFrame()

if "df_detalle" not in st.session_state:
    df_detalle = get(detallePedidoTable)
    st.session_state["df_detalle"] = pd.DataFrame(df_detalle) if df_detalle else pd.DataFrame()

with refresh:
    if st.button("🔄 Refrescar Pedidos"):
        df_pedidos = get(pedidoTable)
        df_detalle = get(detallePedidoTable)
        st.session_state["df_pedidos"] = pd.DataFrame(get(pedidoTable)) if df_pedidos else pd.DataFrame()
        st.session_state["df_detalle"] = pd.DataFrame(get(detallePedidoTable)) if df_detalle else pd.DataFrame()
        st.success("✅ Actualización correcta")
        st.rerun()

df = st.session_state["df_pedidos"]
detalle = st.session_state["df_detalle"]

if not df.empty:
    df = df.dropna(how='all')
    df['created_at'] = pd.to_datetime(df['created_at'])
    df['Fecha'] = df['created_at'].dt.strftime('%d/%m/%Y')

    # Si detalle no está vacío
    if not detalle.empty:
        productos_data = get(productoTable)
        productos = pd.DataFrame(productos_data)

        # Merge para traer nombre del producto
        detalle = detalle.merge(productos[['id', 'nombre']], left_on='nroProducto', right_on='id', how='left')

        # Agrupar detalles por pedido
        detalle_grouped = (
            detalle.groupby("nroPedido")[["nombre", "cantidad"]]
            .apply(lambda x: ", ".join(f"{row['nombre']} x{row['cantidad']}" for _, row in x.iterrows()))
            .reset_index(name="Detalle Pedido")
        )

        # Merge con pedidos
        df = df.merge(detalle_grouped, left_on="id", right_on="nroPedido", how="left")

        # 🔵 Ahora preparamos el DataFrame para mostrar
        # Seleccionamos las columnas que queremos ver en la tabla
        columnas_a_mostrar = [
            "Fecha",      # Fecha creada
            "cliente",    # Nombre del cliente
            "direccion",  # Dirección
            "telefono",   # Teléfono
            "estado",     # Estado del pedido
            "Detalle Pedido",  # Texto con productos
            "total",
        ]

        # Aseguramos que estén todas las columnas (evitar errores si falta alguna)
        columnas_presentes = [col for col in columnas_a_mostrar if col in df.columns]

        tabla_mostrar = df[columnas_presentes]

        # Ahora sí mostramos la tabla
        st.subheader("📝 Tabla de pedidos")
        st.dataframe(tabla_mostrar, use_container_width=True, hide_index=True)
