import streamlit as st
import requests
import base64
from datetime import datetime
import pandas as pd
from io import StringIO

# --- Configuración desde secrets ---
GITHUB_TOKEN = st.secrets["GITHUB_TOKEN"]
REPO = st.secrets["REPO"]
FILE_PATH = st.secrets["FILE_PATH"]

# ============================================================
# =============== FUNCIONES GITHUB (OPTIMIZADAS) ==============
# ============================================================

def github_headers():
    return {
        "Authorization": f"Bearer {GITHUB_TOKEN}",
        "Accept": "application/vnd.github.v3+json"
    }

# --- Guardar registro ---
def append_to_github_csv(cliente, servicio, total, pago, peluquera, propina):
    url = f"https://api.github.com/repos/{REPO}/contents/{FILE_PATH}"

    r = requests.get(url, headers=github_headers())

    # Control de rate limit
    if r.status_code == 403 and "rate limit" in r.text.lower():
        st.error("⛔ GitHub te ha bloqueado temporalmente por exceso de peticiones. Espera 1–2 minutos.")
        return

    data = r.json()

    if "sha" not in data:
        st.error("❌ No se encontró el archivo en GitHub")
        st.code(data)
        return

    sha = data["sha"]
    content = base64.b64decode(data["content"]).decode()

    fecha = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    new_line = f"{fecha},{cliente},{servicio},{total},{pago},{peluquera},{propina}\n"
    new_content = content + new_line

    encoded = base64.b64encode(new_content.encode()).decode()

    r_put = requests.put(url, headers=github_headers(), json={
        "message": "Añadir registro de caja",
        "content": encoded,
        "sha": sha
    })

    if r_put.status_code not in (200, 201):
        st.error("❌ Error al guardar en GitHub")
        st.code(r_put.text)
    else:
        st.success("Cobro registrado correctamente")


# --- Leer CSV con caché ---
@st.cache_data
def load_csv_from_github():
    url = f"https://api.github.com/repos/{REPO}/contents/{FILE_PATH}"

    r = requests.get(url, headers=github_headers())

    if r.status_code == 403 and "rate limit" in r.text.lower():
        st.error("⛔ GitHub te ha bloqueado temporalmente por exceso de peticiones.")
        return pd.DataFrame()

    data = r.json()

    if "content" not in data:
        st.error("❌ No se pudo leer el archivo en GitHub")
        st.code(data)
        return pd.DataFrame()

    content = base64.b64decode(data["content"]).decode()

    # Limpieza automática
    lines = [line for line in content.split("\n") if line.strip() != ""]
    clean_csv = "\n".join(lines)

    try:
        # df = pd.read_csv(pd.compat.StringIO(clean_csv))
        df = pd.read_csv(StringIO(clean_csv))
        return df
    except Exception as e:
        st.error("❌ Error leyendo el CSV")
        st.code(e)
        st.code(clean_csv)
        return pd.DataFrame()


# ============================================================
# ========================= MENÚ ==============================
# ============================================================

menu = st.sidebar.radio("Menú", ["CAJA", "HISTORIAL", "ESTADÍSTICAS"])

# ============================================================
# ========================= CAJA ==============================
# ============================================================

if menu == "CAJA":

    st.title("CAJA")

    # --- Lista de peluqueras con colores ---
    peluqueras = {
        "Vane": "#98ffcc",   # rosa pastel 
        "Virgi": "#c8a2c8",  # lila pastel
        "Merce": "#ffb6c1"   # verde menta 
    }

    st.markdown(" * Peluquera")

    # --- Fila con las tres opciones y el círculo ---
    col_vane, col_virgi, col_merce, col_circle = st.columns([1,1,1,0.5])

    with col_vane:
        if st.button("Vane", use_container_width=True):
            st.session_state.peluquera_activa = "Vane"

    with col_virgi:
        if st.button("Virgi", use_container_width=True):
            st.session_state.peluquera_activa = "Virgi"

    with col_merce:
        if st.button("Merce", use_container_width=True):
            st.session_state.peluquera_activa = "Merce"

    # --- Círculo alineado a la derecha ---
    if "peluquera_activa" in st.session_state:
        color = peluqueras[st.session_state.peluquera_activa]
        with col_circle:
            st.markdown(
                f"""
                <div style="
                    background-color: {color};
                    color: black;
                    width: 60px;
                    height: 60px;
                    border-radius: 50%;
                    display: flex;
                    justify-content: center;
                    align-items: center;
                    font-weight: bold;
                    font-size: 16px;
                    border: 3px solid white;
                    box-shadow: 0px 0px 10px rgba(0,0,0,0.3);
                    margin-top: 10px;
                ">
                    {st.session_state.peluquera_activa}
                </div>
                """,
                unsafe_allow_html=True
            )

#----------------------------------------------------------------------------------------------------------------------

# --- Cargar historial para obtener clientes existentes ---
    df_hist = load_csv_from_github()
    if not df_hist.empty:
        clientes_existentes = sorted(df_hist["cliente"].unique().tolist())
    else:
        clientes_existentes = []

    # --- Selector + campo manual en la misma línea ---
    col_cliente1, col_cliente2 = st.columns(2)

    with col_cliente1:
        cliente_seleccionado = st.selectbox(
            "Cliente existente",
            ["Ninguno"] + clientes_existentes
        )

    with col_cliente2:
        cliente_manual = st.text_input("Cliente manual")

    # --- Lógica final del cliente ---
    if cliente_seleccionado != "Ninguno":
        cliente = cliente_seleccionado
    else:
        cliente = cliente_manual

    if "servicios" not in st.session_state:
        st.session_state.servicios = []

    if "total" not in st.session_state:
        st.session_state.total = 0

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

    st.markdown("### 💶 Total a pagar")
    st.markdown(f"<h1 style='text-align:right;'>{st.session_state.total} €</h1>", unsafe_allow_html=True)

    st.write("Servicios:", ", ".join(st.session_state.servicios))

# --- Pago + Propina ---
    col_pago, col_propina = st.columns(2)

    with col_pago:
        pago = st.radio("Método de pago", ["Efectivo", "Tarjeta"])

    with col_propina:
        propina = st.number_input("Propina (€)", min_value=0, value=0)
    
    # peluquera = st.selectbox("Peluquera", ["Vane", "Merce", "Virgi", "Otra"])
    # # Guardar peluquera activa para mostrarla en el círculo
    # st.session_state.peluquera_activa = peluquera
    

if st.button("💰 COBRAR", use_container_width=True):
    if cliente == "":
        st.error("Pon el nombre de la cliente")
    else:
        servicio_str = "+".join(st.session_state.servicios)
        append_to_github_csv(
            cliente,
            servicio_str,
            st.session_state.total,
            pago,
            st.session_state.peluquera_activa,   # ← aquí estaba el error
            propina
        )

        st.session_state.servicios = []
        st.session_state.total = 0

        # st.success("Cobro registrado correctamente")

        # Meme del hermano de Lamine Yamal en el mundial
        # meme_lamine = "https://i.imgflip.com/92jz8x.jpg"
        meme = https://i.kym-cdn.com/photos/images/newsfeed/002/681/313/4e9.jpg
        st.image(meme, width=250)


# ============================================================
# ======================= HISTORIAL ===========================
# ============================================================

elif menu == "HISTORIAL":

    st.title("📜 Historial de caja")

    df = load_csv_from_github()

    if df.empty:
        st.info("El historial aún está vacío o no se pudo cargar.")
    else:

        # --- FILTRO POR CLIENTE ---
        clientes_unicos = df["cliente"].unique().tolist()
        cliente_filtro = st.selectbox("Filtrar por cliente", ["Todos"] + clientes_unicos)

        if cliente_filtro != "Todos":
            df = df[df["cliente"] == cliente_filtro]

        # --- FILTRO POR PELUQUERA ---
        peluqueras_unicas = df["peluquera"].unique().tolist()
        peluquera_filtro = st.selectbox("Filtrar por peluquera", ["Todas"] + peluqueras_unicas)

        if peluquera_filtro != "Todas":
            df = df[df["peluquera"] == peluquera_filtro]

        st.dataframe(df)

# ============================================================
# ===================== ESTADÍSTICAS ==========================
# ============================================================

elif menu == "ESTADÍSTICAS":

    st.title("📊 Estadísticas")
    st.info("En construcción...")
