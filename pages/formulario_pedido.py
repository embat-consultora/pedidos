import streamlit as st
from streamlit_gsheets import GSheetsConnection
from variables import pedidosNombre, connectionGeneral
from datetime import datetime
import pandas as pd
import logging

def create_gsheets_connection():
    try:
        conn = st.connection(connectionGeneral, type=GSheetsConnection)
        return conn
    except Exception as e:
        st.error(f"Unable to connect to storage: {e}")
        logging.error(e, stack_info=True, exc_info=True)
        return None

# Variable de sesión para controlar si se envió
if "pedido_guardado" not in st.session_state:
    st.session_state.pedido_guardado = False

st.title("📋 Cargar nuevo pedido")

if not st.session_state.pedido_guardado:
    with st.form("formulario_pedido"):
        nombre = st.text_input("Nombre del cliente")
        telefono = st.text_input("Teléfono")
        pedido = st.text_input("Producto")
        cantidad = st.text_input("Cantidad")
        urgente = st.selectbox("¿Es urgente?", ["No", "Sí"])
        direccion = st.text_area("Dirección")

        submitted = st.form_submit_button("Guardar pedido")

    if submitted:
        estado = "Abierto"
        fecha = datetime.now().strftime("%d/%m/%Y")
        urgente_bool = 1 if urgente == "Sí" else 0

        # Crear conexión con Google Sheets
        conn = create_gsheets_connection()
        existing_data = conn.read(worksheet=pedidosNombre)
        nro_pedido = len(existing_data) + 1

        nuevo_pedido = pd.DataFrame([{
            "Nro Pedido": nro_pedido,
            "Fecha": fecha,
            "Cliente": nombre,
            "Pedido": pedido,
            "Cantidad": cantidad,
            "Direccion": direccion,
            "Telefono": telefono,
            "Urgente": urgente_bool,
            "Estado": estado
        }])

        nuevo_pedido = nuevo_pedido[existing_data.columns]
        updated_data = pd.concat([existing_data, nuevo_pedido], ignore_index=True)
        conn.update(worksheet=pedidosNombre, data=updated_data)

        st.session_state.pedido_guardado = True
        st.rerun()  # Refresca la página para ocultar el formulario

else:
    st.success("✅ El pedido fue guardado correctamente.")
    st.button("Cargar otro pedido", on_click=lambda: st.session_state.update({"pedido_guardado": False}))
