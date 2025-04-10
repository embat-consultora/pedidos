import streamlit as st
from streamlit_gsheets import GSheetsConnection
from variables import pedidosNombre, detalleNombre, productoNombre, connectionGeneral
from datetime import datetime
import pandas as pd
import logging

# Conexión a Google Sheets
def create_gsheets_connection():
    try:
        conn = st.connection(connectionGeneral, type=GSheetsConnection)
        return conn
    except Exception as e:
        st.error(f"No se pudo conectar con el almacenamiento: {e}")
        logging.error(e, stack_info=True, exc_info=True)
        return None

# Variables de sesión
if "pedido_guardado" not in st.session_state:
    st.session_state.pedido_guardado = False

if "productos_cliente" not in st.session_state:
    st.session_state.productos_cliente = []

st.title("📋 Cargar nuevo pedido")

# Conectarse y obtener lista de productos
conn = create_gsheets_connection()
productos_disponibles = []

if conn:
    productos_data = conn.read(worksheet=productoNombre)
    if not productos_data.empty and "Producto" in productos_data.columns:
        productos_disponibles = productos_data["Producto"].dropna().tolist()

if not productos_disponibles:
    st.warning("⚠️ No hay productos cargados aún.")
else:
    if not st.session_state.pedido_guardado:
        with st.form("formulario_pedido"):
            st.subheader("🧾 Datos del cliente")
            nombre = st.text_input("Nombre del cliente")
            telefono = st.text_input("Teléfono")
            direccion = st.text_area("Dirección")
            urgente = st.selectbox("¿Es urgente?", ["No", "Sí"])

            st.subheader("📦 Agregar producto")
            col1, col2 = st.columns([3, 1])
            producto_seleccionado = col1.selectbox("Producto", productos_disponibles)
            cantidad = col2.number_input("Cantidad", min_value=1, step=1)

            agregar = st.form_submit_button("➕ Agregar producto al pedido")

            if agregar:
                st.session_state.productos_cliente.append({
                    "producto": producto_seleccionado,
                    "cantidad": cantidad
                })
                st.rerun()

            if st.session_state.productos_cliente:
                st.markdown("### 🛒 Productos agregados:")
                for idx, p in enumerate(st.session_state.productos_cliente, start=1):
                    st.markdown(f"- {p['producto']} x{p['cantidad']}")

            st.markdown("---")
            enviar = st.form_submit_button("✅ Guardar pedido completo")

            if enviar:
                if not nombre.strip():
                    st.error("⚠️ Ingresá el nombre del cliente.")
                elif not st.session_state.productos_cliente:
                    st.error("⚠️ Debés agregar al menos un producto.")
                else:
                    fecha = datetime.now().strftime("%d/%m/%Y")
                    urgente_bool = 1 if urgente == "Sí" else 0

                    # Leer datos actuales
                    pedidos_df = conn.read(worksheet=pedidosNombre)
                    detalle_df = conn.read(worksheet=detalleNombre)

                    nro_pedido = len(pedidos_df) + 1 if not pedidos_df.empty else 1

                    # Crear fila para hoja pedidos
                    pedido_general = pd.DataFrame([{
                        "Nro Pedido": nro_pedido,
                        "Fecha": fecha,
                        "Cliente": nombre.strip(),
                        "Direccion": direccion.strip(),
                        "Telefono": telefono.strip(),
                        "Urgente": urgente_bool,
                        "Estado": "Abierto"
                    }])

                    pedido_general = pedido_general[pedidos_df.columns] if not pedidos_df.empty else pedido_general
                    pedidos_actualizados = pd.concat([pedidos_df, pedido_general], ignore_index=True)

                    # Crear filas para hoja detalle
                    detalle_nuevo = pd.DataFrame([
                        {
                            "Nro Pedido": nro_pedido,
                            "Producto": p["producto"],
                            "Cantidad": p["cantidad"]
                        }
                        for p in st.session_state.productos_cliente
                    ])

                    detalle_nuevo = detalle_nuevo[detalle_df.columns] if not detalle_df.empty else detalle_nuevo
                    detalle_actualizado = pd.concat([detalle_df, detalle_nuevo], ignore_index=True)

                    # Guardar ambos
                    conn.update(worksheet=pedidosNombre, data=pedidos_actualizados)
                    conn.update(worksheet=detalleNombre, data=detalle_actualizado)

                    st.success("✅ El pedido fue guardado correctamente.")
                    st.session_state.pedido_guardado = True
                    st.session_state.productos_cliente = []
                    st.rerun()

    else:
        st.success("✅ El pedido fue guardado correctamente.")
        st.button("Cargar otro pedido", on_click=lambda: st.session_state.update({
            "pedido_guardado": False,
            "productos_cliente": []
        }))
