import streamlit as st
import pandas as pd
from datetime import datetime
import logging
from modules.data_base import get, add
from variables import pedidoTable, detallePedidoTable, productoTable, page_icon  # <-- tablas en Supabase

st.set_page_config(
    page_title="Formulario Pedido",
    page_icon=page_icon,
)

# Variables de sesión
if "pedido_guardado" not in st.session_state:
    st.session_state.pedido_guardado = False

if "productos_cliente" not in st.session_state:
    st.session_state.productos_cliente = []

st.title("📋 Nuevo pedido")

# Obtener lista de productos desde Supabase
productos_disponibles = []
precios_dict = {}
productos_data = get(productoTable)

if productos_data:
    productos_df = pd.DataFrame(productos_data)
    if not productos_df.empty and "nombre" in productos_df.columns:
        productos_df = productos_df.dropna(subset=["nombre"])
        productos_disponibles = productos_df["nombre"].tolist()
        precios_dict = dict(zip(productos_df["nombre"], productos_df["precio"]))

if not productos_disponibles:
    st.warning("⚠️ No hay productos cargados aún.")
else:
    if not st.session_state.pedido_guardado:

        # ----------------------
        # SECCIÓN FUERA DEL FORM
        # ----------------------
        st.subheader("📦 Agregar producto")

        col1, col2, col3 = st.columns([3, 1, 1])
        producto_seleccionado = col1.selectbox("Producto", productos_disponibles, key="producto_actual")
        cantidad = col2.number_input("Cantidad", min_value=1, step=1, key="cantidad_actual")
        with col3:
            precio_unitario = precios_dict.get(producto_seleccionado, 0)
            st.text(f"Precio: ${precio_unitario:.2f}")

        subtotal = precio_unitario * cantidad
        st.write(f"Subtotal: ${subtotal:.2f}")

        if st.button("➕ Agregar producto al pedido"):
            st.session_state.productos_cliente.append({
                "producto": producto_seleccionado,
                "cantidad": cantidad,
                "subtotal": subtotal
            })
            st.rerun()

        if st.session_state.productos_cliente:
            st.markdown("### 🛒 Productos agregados:")
            total_general = 0
            for idx, p in enumerate(st.session_state.productos_cliente, start=1):
                total_general += p["subtotal"]
                st.markdown(f"- {p['producto']} x{p['cantidad']} → ${p['subtotal']:.2f}")
            st.markdown(f"### 💵 Total del pedido: ${total_general:.2f}")
        else:
            total_general = 0

        # ----------------------
        # FORMULARIO DEL PEDIDO
        # ----------------------
        st.markdown("---")
        with st.form("formulario_pedido"):
            st.subheader("🧾 Datos del cliente")
            nombre = st.text_input("Nombre y Apellido")
            telefono = st.text_input("Teléfono")
            direccion = st.text_area("Dirección")
            urgente = st.selectbox("¿Es urgente?", ["No", "Sí"])

            enviar = st.form_submit_button("✅ Completar Pedido")

        if enviar:
            if not nombre.strip():
                st.error("⚠️ Ingresá el nombre del cliente.")
            elif not st.session_state.productos_cliente:
                st.error("⚠️ Debés agregar al menos un producto.")
            else:
                urgente_bool = 1 if urgente == "Sí" else 0

                try:
                    # Crear el pedido
                    pedido_data = {
                        "cliente": nombre.strip(),
                        "direccion": direccion.strip(),
                        "telefono": telefono.strip(),
                        "urgencia": urgente_bool,
                        "estado": "Abierto",
                        "total": total_general
                    }
                    pedido_response = add(pedidoTable, pedido_data)
                    # Obtener el ID o el NroPedido generado (depende de cómo esté configurado tu Supabase)
                    nro_pedido = pedido_response.data[0]["id"]  # o "Nro Pedido" si lo guardás así
                 
                    # Agregar los productos al detallePedido
                    for p in st.session_state.productos_cliente:
                        producto_info = productos_df[productos_df["nombre"] == p["producto"]].iloc[0]
                        st.write(producto_info["id"])
                        detalle_data = {
                            "nroProducto": int(producto_info["id"]), 
                            "nroPedido": int(nro_pedido),           
                            "cantidad": int(p["cantidad"]),      
                            "precio": float(p["subtotal"])    
                        }
                        add(detallePedidoTable, detalle_data)

                    st.success("✅ El pedido fue enviado correctamente.")
                    st.session_state.pedido_guardado = True
                    st.session_state.productos_cliente = []
                    st.rerun()

                except Exception as e:
                    logging.error(e, stack_info=True, exc_info=True)
                    st.error(f"❌ Error al enviar el pedido: {e}")

    else:
        st.success("✅ El pedido fue enviado correctamente.")
        st.button("Cargar otro pedido", on_click=lambda: st.session_state.update({
            "pedido_guardado": False,
            "productos_cliente": []
        }))
