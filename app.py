import streamlit as st

# st.title("Caja Peluquería")
# st.write("App inicial lista para conectar con GitHub CSV")

import requests
import base64
from datetime import datetime
import pandas as pd

# --- Configuración desde secrets ---
GITHUB_TOKEN = st.secrets["GITHUB_TOKEN"]
REPO = st.secrets["REPO"]          # ej: "ana/peluqueria-caja"
FILE_PATH = st.secrets["FILE_PATH"]  # ej: "historial.csv"

# --- Función para añadir registro al CSV en GitHub ---
def append_to_github_csv(cliente, servicio, total):
    url = f"https://api.github.com/repos/{REPO}/contents/{FILE_PATH}"
    headers = {"Authorization": f"token {GITHUB_TOKEN}"}

    # Obtener contenido actual
    r = requests.get(url, headers=headers).json()
    sha = r["sha"]
    content = base64.b64decode(r["content"]).decode()

    # Nueva línea
    fecha = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    new_line = f"{fecha},{cliente},{servicio},{total}\n"
    new_content = content + new_line

    # Subir archivo actualizado
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

# --- Interfaz Streamlit ---
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

with col2:
    if st.button("🧴 Lavado (+5€)", use_container_width=True):
        st.session_state.servicios.append("lavado")
        st.session_state.total += 5

st.subheader(f"Total: {st.session_state.total} €")
st.write("Servicios:", ", ".join(st.session_state.servicios))

# Botón cobrar
if st.button("💰 COBRAR", use_container_width=True):
    if cliente == "":
        st.error("Pon el nombre de la cliente")
    else:
        servicio_str = "+".join(st.session_state.servicios)
        append_to_github_csv(cliente, servicio_str, st.session_state.total)
        st.success("Cobro registrado correctamente")

        # Reset
        st.session_state.servicios = []
        st.session_state.total = 0

# Mostrar historial
st.subheader("📜 Historial de caja")
try:
    df = load_csv_from_github()
    st.dataframe(df)
except:
    st.info("El historial aún está vacío o no se pudo cargar.")

