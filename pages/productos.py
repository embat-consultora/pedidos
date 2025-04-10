import streamlit as st
from navigation import make_sidebar
from streamlit_gsheets import GSheetsConnection
from variables import productoNombre, connectionGeneral
import pandas as pd
import logging
from page_utils import apply_page_config
from sheet_connection import create_gsheets_connection

# Configuración inicial
apply_page_config()

# Control de acceso
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

# Conexión


st.title("📦 Gestión de Stock de Productos")

conn = create_gsheets_connection(connectionGeneral)

# 🔄 Cargar productos desde sesión o Google Sheets
if conn:
    if "Stock" not in st.session_state:
        productos_df = conn.read(worksheet=productoNombre)
        if productos_df is not None and not productos_df.empty:
            st.session_state["Stock"] = productos_df.copy()
        else:
            st.session_state["Stock"] = pd.DataFrame(columns=["Producto", "Stock"])

    if st.button("🔄 Refrescar"):
        productos_actualizados = conn.read(worksheet=productoNombre)
        if productos_actualizados is not None and not productos_actualizados.empty:
            st.session_state["Stock"] = productos_actualizados.copy()
            st.success("✅ Productos actualizados")
            st.rerun()
        else:
            st.warning("⚠️ No se pudo actualizar la lista de productos.")

    productos_df = st.session_state["Stock"]

    # Mostrar tabla de productos
    if productos_df.empty or "Producto" not in productos_df.columns:
        st.warning("⚠️ No hay productos cargados aún.")
        productos_df = pd.DataFrame(columns=["Producto", "Stock"])
    else:
        productos_df["Stock"] = productos_df["Stock"].fillna(0).astype(int)
        st.subheader("📋 Productos actuales:")
        st.dataframe(productos_df, use_container_width=True, hide_index=True)

    # ➕➖ Formulario para actualizar stock
    with st.expander("Agregar / Consumir Stock", expanded=False):
        with st.form("form_stock"):
            producto = st.selectbox("Producto", productos_df["Producto"].tolist())
            accion = st.radio("¿Qué querés hacer?", ["Agregar", "Consumir"], horizontal=True)
            cantidad = st.number_input("Cantidad", min_value=1, step=1)
            procesar = st.form_submit_button("Actualizar stock")

        if procesar:
            if producto in productos_df["Producto"].values:
                idx = productos_df[productos_df["Producto"] == producto].index[0]
                if accion == "Agregar":
                    productos_df.at[idx, "Stock"] += cantidad
                    st.success(f"✅ Se agregaron {cantidad} unidades a '{producto}'")
                else:
                    if productos_df.at[idx, "Stock"] >= cantidad:
                        productos_df.at[idx, "Stock"] -= cantidad
                        st.success(f"✅ Se consumieron {cantidad} unidades de '{producto}'")
                    else:
                        st.error("❌ No hay suficiente stock para consumir esa cantidad.")

                st.session_state["Stock"] = productos_df.copy()
                conn.update(worksheet=productoNombre, data=productos_df)
                st.rerun()

    # 🆕 Formulario para agregar nuevo producto
    with st.expander("Agregar nuevo producto", expanded=False):
        with st.form("form_nuevo_producto"):
            nuevo_producto = st.text_input("Nombre del producto").strip()
            stock_inicial = st.number_input("Stock inicial", min_value=0, step=1)
            agregar_producto = st.form_submit_button("Agregar producto")

        if agregar_producto:
            if not nuevo_producto:
                st.warning("⚠️ Ingresá un nombre válido.")
            elif nuevo_producto in productos_df["Producto"].values:
                st.warning("⚠️ El producto ya existe.")
            else:
                nuevo = pd.DataFrame([{
                    "Producto": nuevo_producto,
                    "Stock": stock_inicial
                }])
                productos_df = pd.concat([productos_df, nuevo], ignore_index=True)
                st.session_state["Stock"] = productos_df.copy()
                conn.update(worksheet=productoNombre, data=productos_df)
                st.success(f"✅ Producto '{nuevo_producto}' agregado con {stock_inicial} unidades.")
                st.rerun()
