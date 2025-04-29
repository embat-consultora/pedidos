import streamlit as st
from navigation import make_sidebar
from streamlit_gsheets import GSheetsConnection
import pandas as pd
from page_utils import apply_page_config
from modules.data_base import get, add

# Configuración inicial
apply_page_config()

# Control de acceso
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

st.title("📦 Productos y Stock")
tabla = "producto"

# 🆕 Cargar productos
if "productos" not in st.session_state:
    st.session_state.productos = get(tabla)

# Botón refrescar
if st.button("🔄 Refrescar"):
    st.session_state.productos = get(tabla)

productos = st.session_state.productos
prods = pd.DataFrame(productos)

# Solo si hay productos
if not prods.empty:
    columnas_visibles = {
        "nombre": "Producto",
        "stock": "Stock",
        "precio": "Precio"
    }
    prods = prods[list(columnas_visibles.keys())]  # Filtramos las columnas deseadas
    prods.rename(columns=columnas_visibles, inplace=True)
    st.dataframe(prods, use_container_width=True, hide_index=True)
else:
    st.info("Todavía no hay productos cargados.")

# 🆕 Formulario para agregar nuevo producto
with st.expander("Agregar nuevo producto", expanded=False):
    with st.form("form_nuevo_producto"):
        nombre = st.text_input("Nombre del producto").strip()
        stock_inicial = st.number_input("Stock inicial", min_value=0, step=1)
        precio = st.text_input("Precio")
        agregar_producto = st.form_submit_button("Agregar producto")

    if agregar_producto:
        if nombre and stock_inicial and precio:
            data = {
                "nombre": nombre,
                "stock": stock_inicial,
                "precio": precio
            }
            try:
                add(tabla, data)
                st.success(f"Producto '{nombre}' creado correctamente.")
                st.session_state.productos = get(tabla)  # Refrescamos productos
                st.rerun()
            except Exception as e:
                st.error(f"Ocurrió un error al guardar el producto: {e}")
        else:
            st.warning("Por favor completá todos los campos.")
