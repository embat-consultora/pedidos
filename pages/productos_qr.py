import streamlit as st
from navigation import make_sidebar
import pandas as pd
from page_utils import apply_page_config
from modules.data_base import get
import qrcode
import io

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
        "cantidad_pack": "Cantidad Pack",
        "precio": "Precio"
    }
    prodsFiltered = prods[list(columnas_visibles.keys())]  # Filtramos las columnas deseadas
    prodsFiltered.rename(columns=columnas_visibles, inplace=True)
    st.dataframe(prodsFiltered, use_container_width=True, hide_index=True)
else:
    st.info("Todavía no hay productos cargados.")

# -----------------------------
# Generar QR
# -----------------------------
st.subheader("Generar QR de un producto")
if not prods.empty:
    producto_sel = st.selectbox("Selecciona producto", prods["nombre"].tolist())
   
    if st.button("Generar QR") and producto_sel:
        prod = prods[prods["nombre"] == producto_sel].iloc[0]
        base_url = st.secrets["urls"]["qr_url"]
        codigo = str(prod["id"])
        pack = int(prod["cantidad_pack"])

        # Generamos la URL con query params
        qr_url = f"{base_url}/qr?codigo={codigo}&pack={pack}"
        # Generamos QR con esa URL
        qr = qrcode.make(qr_url)
        # Generar QR
        buf = io.BytesIO()
        qr.save(buf, format="PNG")

        st.image(buf.getvalue())
        st.download_button("Descargar QR", buf.getvalue(),
                           file_name=f"{prod['id']}_qr.png",
                           mime="image/png")
