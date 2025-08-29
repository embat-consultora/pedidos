import streamlit as st
from modules.data_base import updateProductQR
import pandas as pd
tabla = "producto"

params = st.query_params
if "codigo" in params and "pack" in params:
    codigo = params["codigo"]
    pack = int(params["pack"])
    funcion = 'stock - {pack}'
    updateProductQR(tabla, codigo, funcion)
    st.success(f"✅ Stock actualizado para {codigo}: -{pack}")
else:
    st.error("❌ Producto no encontrado.")
