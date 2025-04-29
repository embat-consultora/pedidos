import streamlit as st
from navigation import make_sidebar
from page_utils import apply_page_config
import pandas as pd
from datetime import datetime
from modules.data_base import get, updateEstadoPedido
from variables import pedidoTable, detallePedidoTable, productoTable
from fpdf import FPDF
import tempfile
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

st.title("📋 Pedidos")

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

    # Formato de fechas
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
    else:
        df["Detalle Pedido"] = "Sin detalles"

    # Filtros
    with filtros:
        filtro = st.radio(
            "📌 Filtrar pedidos por:",
            ("Todos", "Solo urgentes", "Solo de hoy", "Urgentes de hoy", "Listos de hoy"),
            horizontal=True
        )

    hoy_str = datetime.now().strftime("%d/%m/%Y")

    # Aplicar filtros
    if filtro == "Solo urgentes":
        df = df[(df["urgencia"] == 1) & (df["estado"] == "Abierto")]
    elif filtro == "Solo de hoy":
        df = df[(df["Fecha"] == hoy_str) & (df["estado"] == "Abierto")]
    elif filtro == "Urgentes de hoy":
        df = df[(df["urgencia"] == 1) & (df["Fecha"] == hoy_str) & (df["estado"] == "Abierto")]
    elif filtro == "Listos de hoy":
        df = df[(df["estado"] == "Listo") & (df["Fecha"] == hoy_str)]
    else:
        df = df[df["estado"] == "Abierto"]

    if df.empty:
        st.warning("⚠️ No hay pedidos que coincidan con los filtros seleccionados.")
    else:
        st.subheader("📦 Pedidos encontrados")
        for index, row in df.iterrows():
            with st.expander(f"Pedido #{row['id']} - {row['cliente']}"):
                st.write(f"📅 Fecha: {row['Fecha']}")
                st.write(f"📝 Total $: {row['total']}")
                st.write(f"📝 Productos: {row['Detalle Pedido']}")
                st.write(f"📍 Dirección: {row['direccion']}")
                st.write(f"📞 Teléfono: {str(int(float(row['telefono'])))}")
                st.write(f"🚨 Urgente: {'Sí' if row['urgencia'] == 1 else 'No'}")
                st.write(f"📌 Estado: {row['estado']}")

                if row['estado'] == "Abierto":
                    if st.button(f"✅ Marcar como Listo (Pedido #{row['id']})", key=f"boton_listo_{index}"):
                        try:
                            pedido_id = row['id']
                            updateEstadoPedido(pedido_id, "Listo")
                            df_pedidos = get(pedidoTable)
                            df_detalle = get(detallePedidoTable)
                            st.session_state["df_pedidos"] = pd.DataFrame(df_pedidos) if df_pedidos else pd.DataFrame()
                            st.session_state["df_detalle"] = pd.DataFrame(df_detalle) if df_detalle else pd.DataFrame()
                            st.success(f"Pedido #{row['id']} marcado como Listo ✅")
                            st.rerun()
                        except Exception as e:
                            st.error(f"❌ Error actualizando el pedido: {e}")

                if row['estado'] == "Listo":
                    if st.button(f"🧾 Generar factura (Pedido #{row['id']})", key=f"boton_factura_{index}"):
                        try:
                            # Crear el PDF
                            pdf = FPDF()
                            pdf.add_page()
                            pdf.set_font("Arial", size=12)

                            # Encabezado
                            pdf.cell(200, 10, txt="Factura de Pedido", ln=True, align="C")
                            pdf.ln(10)

                            # Datos del cliente
                            pdf.cell(200, 10, txt=f"Cliente: {row['cliente']}", ln=True)
                            pdf.cell(200, 10, txt=f"Fecha: {row['Fecha']}", ln=True)
                            pdf.cell(200, 10, txt=f"Teléfono: {str(int(float(row['telefono'])))}", ln=True)
                            pdf.cell(200, 10, txt=f"Dirección: {row['direccion']}", ln=True)
                            pdf.ln(10)

                            # Detalle de productos
                            pdf.cell(200, 10, txt="Detalle del pedido:", ln=True)
                            pdf.multi_cell(0, 10, row['Detalle Pedido'])
                            pdf.ln(10)

                            # Total
                            pdf.cell(200, 10, txt=f"Total: ${row['total']:.2f}", ln=True)

                            # Guardar a un archivo temporal
                            with tempfile.NamedTemporaryFile(delete=False, suffix=".pdf") as tmpfile:
                                pdf.output(tmpfile.name)
                                st.success("✅ Factura generada correctamente.")

                                # Mostrar botón de descarga
                                with open(tmpfile.name, "rb") as file:
                                    st.download_button(
                                        label="⬇️ Descargar Factura",
                                        data=file,
                                        file_name=f"Factura_Pedido_{row['id']}.pdf",
                                        mime="application/pdf"
                                    )
                        except Exception as e:
                            st.error(f"❌ Error generando la factura: {e}")

else:
    st.info("Aquí encontrarás tus pedidos. Todavía no tienes pedidos cargados.")
