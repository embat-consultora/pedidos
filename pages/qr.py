import streamlit as st
from modules.data_base import updateProductStock, getProductStockById
import pandas as pd
tabla = "producto"

params = st.query_params
if "codigo" in params and "pack" in params:
    codigo = params["codigo"]
    pack = int(params["pack"])
    stockProduct =getProductStockById(tabla, codigo)
    newStock= int(stockProduct.data[0]["stock"]) - pack
    updateProductStock(tabla, codigo, newStock)
    st.success(f"✅ Stock actualizado para {stockProduct.data[0]["nombre"]}: -{pack}")
else:
    st.error("❌ Producto no encontrado.")
