import streamlit as st
import requests
import base64
from datetime import datetime
import pandas as pd

# --- Configuración desde secrets ---
GITHUB_TOKEN = st.secrets["GITHUB_TOKEN"]
REPO = st.secrets["REPO"]
FILE_PATH = st.secrets["FILE_PATH"]

# --- Función para añadir registro al CSV en GitHub ---
def append_to_github_csv(cliente, servicio, total, pago, peluquera, propina):
    url = f"https://api.github.com/repos/{REPO}/contents/{FILE_PATH}"
    headers = {"Authorization": f"token {GITHUB_TOKEN}"}

    r = requests.get(url, headers=headers).json()
    sha = r["sha"]
    content = base64.b64decode(r["content"]).decode()

    fecha = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    new_line = f"{fecha},{cliente},{servicio},{total},{pago},{peluquera},{propina}\n"
    new_content = content + new_line

    encoded = base64.b64encode(new_content.encode()).decode()

    requests.put(url, headers=headers, json={
        "message": "Añadir registro de caja",
        "content": encoded,
        "sha": sha
    })

# --- Función para leer el CSV desde GitHub ---
def load_csv_from_github():
    url = f"https://api.github.com/repos/{REPO}/contents/{FILE_PATH}"
    headers = {"Authorization": f"token {GITHUB_TOKEN}"}
    r = requests.get(url, headers=headers).json()
    content = base64.b64decode(r["content"]).decode()
    df = pd.read_csv(pd.compat.StringIO(content))
    return df

# --- Menú lateral ---
menu = st.sidebar.radio("Menú", ["CAJA", "HISTORIAL", "ESTADÍSTICAS"])

# ============================================================
# ========================= CAJA ==============================
# ============================================================
if menu == "CAJA":

    st.title("CAJA")

    cliente = st.text_input("Nombre de la cliente")

    # Servicios seleccionados
    if "servicios" not in st.session_state:
        st.session_state.servicios = []

    if "total" not in st.session_state:
        st.session_state.total = 0

    # Botones grandes
    st.markdown("""
    <style>
    button {
        height: 80px !important;
        font-size: 28px !important;
    }
    </style>
    """, unsafe_allow_html=True)

    col1, col2 = st.columns(2)

    with col1:
        if st.button("✂️ Corte (+15€)", use_container_width=True):
            st.session_state.servicios.append("corte")
            st.session_state.total += 15

        if st.button("🎨 Tinte (+25€)", use_container_width=True):
            st.session_state.servicios.append("tinte")
            st.session_state.total += 25

    with col2:
        if st.button("🧴 Lavado (+5€)", use_container_width=True):
            st.session_state.servicios.append("lavado")
            st.session_state.total += 5

        extra = st.number_input("Extra manual (€)", min_value=0, value=0)
        if extra > 0:
            st.session_state.servicios.append(f"extra:{extra}")
            st.session_state.total += extra

    # Total a la derecha
    st.markdown("### 💶 Total a pagar")
    st.markdown(f"<h1 style='text-align:right;'>{st.session_state.total} €</h1>", unsafe_allow_html=True)

    st.write("Servicios:", ", ".join(st.session_state.servicios))

    # Método de pago
    pago = st.radio("Método de pago", ["Efectivo", "Tarjeta"])

    # Peluquera
    peluquera = st.selectbox("Peluquera", ["Ana", "María", "Lucía", "Otra"])

    # Propina
    propina = st.number_input("Propina (€)", min_value=0, value=0)

    # Botón cobrar
    if st.button("💰 COBRAR", use_container_width=True):
        if cliente == "":
            st.error("Pon el nombre de la cliente")
        else:
            servicio_str = "+".join(st.session_state.servicios)
            append_to_github_csv(cliente, servicio_str, st.session_state.total, pago, peluquera, propina)
            st.success("Cobro registrado correctamente")

            # Reset
            st.session_state.servicios = []
            st.session_state.total = 0

# ============================================================
# ======================= HISTORIAL ===========================
# ============================================================
elif menu == "HISTORIAL":

    st.title("📜 Historial de caja")

    try:
        df = load_csv_from_github()
        st.dataframe(df)
    except:
        st.info("El historial aún está vacío o no se pudo cargar.")

# ============================================================
# ===================== ESTADÍSTICAS ==========================
# ============================================================
elif menu == "ESTADÍSTICAS":

    st.title("📊 Estadísticas")
    st.info("En construcción...")
