import requests
import streamlit as st
import folium
from streamlit_folium import st_folium
from openrouteservice import convert
from geopy.distance import geodesic
import pandas as pd

# ---------------------------
# Funções de suporte
# ---------------------------

# Cache do arquivo de pedágios
@st.cache_data(show_spinner=False)
def load_pedagios():
    df = pd.read_excel("./database/pracas.xlsx", usecols=["praca", "rodovia", "lat", "lon", "valor_leve"])
    return df

# Cache da API de rotas
@st.cache_data(show_spinner=False)
def fetch_api_cache(remetente, destinatario):
    coord_origem = get_coords(remetente)
    coord_destino = get_coords(destinatario)

    if not coord_origem or not coord_destino:
        return None

    ORS_API_KEY = "eyJvcmciOiI1YjNjZTM1OTc4NTExMTAwMDFjZjYyNDgiLCJpZCI6Ijc4NDkzZWRjZThhMTQ4NjZiMGUwNzMxNTA5MzI3Zjk3IiwiaCI6Im11cm11cjY0In0="
    url = "https://api.openrouteservice.org/v2/directions/driving-car"
    headers = {"Authorization": ORS_API_KEY}
    body = {
        "coordinates": [
            [coord_origem[1], coord_origem[0]],
            [coord_destino[1], coord_destino[0]]
        ]
    }
    try:
        return requests.post(url, json=body, headers=headers).json()
    except Exception:
        return None

def get_coords(endereco):
    url = "https://nominatim.openstreetmap.org/search"
    params = {"q": endereco, "format": "json"}
    headers = {"User-Agent": "MeuApp/1.0 (email@exemplo.com)"}
    resp = requests.get(url, params=params, headers=headers)
    if resp.status_code != 200:
        return None
    try:
        dados = resp.json()
    except ValueError:
        return None
    if not dados:
        return None
    return float(dados[0]["lat"]), float(dados[0]["lon"])

def calcular_pedagios(coords, tipo_veiculo):
    df = load_pedagios()
    pedagios_rota = []

    # Reduz pontos da rota para acelerar
    rota_pontos = coords[::20]

    for _, row in df.iterrows():
        pedagio_coord = (row["lat"], row["lon"])
        for ponto in rota_pontos:
            distancia = geodesic(ponto, pedagio_coord).km
            if distancia < 5:
                valor = row.get("valor_leve", 0)
                pedagios_rota.append({
                    "nome": row["praca"],
                    "rodovia": row["rodovia"],
                    "valor": valor,
                    "lat": row["lat"],
                    "lon": row["lon"]
                })
                break
    return pedagios_rota

# ---------------------------
# App Streamlit
# ---------------------------

def Cargas():
    st.set_page_config(page_title="Cargas", layout="wide")
    st.title("🚚 Frete Minimo")

    col1, col2, col3 = st.columns([1, 2, 2])
    type_vehicle = col1.selectbox(
        "🚗 Tipo de veículo:",
        options=("Carreta", "Carreta Trucada", "Truck", "Rodo-trem", "Vanderleia"),
        index=0
    )
    remetente = col2.text_input("🚩 Remetente:", value="Av. Miguel Pastuszak, 532")
    destinatario = col3.text_input("🚩 Destinatário:", value="R. Mansueto Bossardi, 375")

    rota = fetch_api_cache(remetente, destinatario)
    if not rota or "routes" not in rota:
        st.error("Não foi possível obter a rota.")
        st.json(rota)
        return

    # Distância e tempo
    summary = rota['routes'][0]['summary']
    distancia_km = summary['distance'] / 1000
    duracao_h = summary['duration'] / 3600

    col1, col2, col3 = st.columns(3)
    col1.metric("Distância (km)", f"{distancia_km:.2f}")
    col2.metric("Tempo estimado (h)", f"{duracao_h:.2f}")

    # Decodificar rota
    geometry = rota["routes"][0]["geometry"]
    coords = convert.decode_polyline(geometry)["coordinates"]
    coords = [(lat, lon) for lon, lat in coords]

    # Calcular pedágios
    pedagios_rota = calcular_pedagios(coords, type_vehicle)
    total_pedagio = sum([p["valor"] for p in pedagios_rota])
    col3.metric("Valor pedágio (R$)", f"{total_pedagio:.2f}")

    # Criar mapa
    mapa = folium.Map(location=coords[0], zoom_start=10)
    folium.PolyLine(coords[::5], color="blue", weight=5).add_to(mapa)  # reduz pontos para plot
    folium.Marker(coords[0], tooltip="Origem").add_to(mapa)
    folium.Marker(coords[-1], tooltip="Destino").add_to(mapa)

    # Marcar pedágios
    for p in pedagios_rota:
        folium.Marker(
            location=(p["lat"], p["lon"]),
            popup=f"{p['nome']} - {p['rodovia']} - R${p['valor']:.2f}",
            icon=folium.Icon(color="red", icon="road", prefix="fa")
        ).add_to(mapa)

    st_folium(mapa, center=True, use_container_width=True, height=500)

# ---------------------------
# Executar app
# ---------------------------
Cargas()
