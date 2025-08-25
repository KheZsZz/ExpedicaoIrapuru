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

@st.cache_data
def load_pedagios():
    # Carrega Excel e padroniza nomes de colunas
    df = pd.read_excel("database/pracas.xlsx")  
    df.columns = (
        df.columns.str.strip()
        .str.lower()
        .str.replace(" ", "_")  # transforma "Valor Leve" em "valor_leve"
    )
    # Remove linhas sem coordenadas
    df = df.dropna(subset=["lat", "lon"])
    df["lat"] = df["lat"].astype(float)
    df["lon"] = df["lon"].astype(float)
    return df

def calcular_pedagios(coords):
    df = load_pedagios()
    pedagios_rota = []
    total_valor = 0

    # Adiciona coluna de tupla de coordenadas
    df["coords"] = list(zip(df["lat"], df["lon"]))

    for ponto in coords:
        # Filtra pedágios próximos (<5 km)
        proximos = df[df["coords"].apply(lambda c: geodesic(c, ponto).km < 5)]
        for _, row in proximos.iterrows():
            valor = float(row.get("valor_leve", 0))
            pedagios_rota.append({
                "nome": row["praca"],
                "rodovia": row.get("rodovia", ""),
                "valor": valor,
                "lat": row["lat"],
                "lon": row["lon"]
            })
            total_valor += valor

    return pedagios_rota, total_valor

def get_coords(endereco):
    url = "https://nominatim.openstreetmap.org/search"
    params = {"q": endereco, "format": "json"}
    headers = {"User-Agent": "MeuApp/1.0 (email@exemplo.com)"}
    resp = requests.get(url, params=params, headers=headers)
    if resp.status_code != 200:
        return None
    dados = resp.json()
    if not dados:
        return None
    return float(dados[0]["lat"]), float(dados[0]["lon"])

def fetch_api(remetente, destinatario):
    coord_origem = get_coords(remetente)
    coord_destino = get_coords(destinatario)
    if not coord_origem or not coord_destino:
        return None

    ORS_API_KEY = "SUA_CHAVE_ORS_AQUI"
    url = "https://api.openrouteservice.org/v2/directions/driving-car"
    headers = {"Authorization": ORS_API_KEY}
    body = {
        "coordinates": [
            [coord_origem[1], coord_origem[0]],
            [coord_destino[1], coord_destino[0]]
        ]
    }
    resp = requests.post(url, json=body, headers=headers)
    if resp.status_code != 200:
        st.error(f"Erro ORS API: {resp.status_code}")
        return None
    return resp.json()

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

    rota = fetch_api(remetente, destinatario)
    if not rota or "routes" not in rota:
        st.error("Não foi possível obter a rota.")
        st.json(rota)
        return

    # ---------------------------
    # Métricas de distância, tempo e frete
    # ---------------------------
    summary = rota['routes'][0]['summary']
    distancia_km = summary['distance'] / 1000
    duracao_h = summary['duration'] / 3600

    col1, col2, col3 = st.columns(3)
    col1.metric("Distância (km)", f"{distancia_km:.2f}")
    col2.metric("Tempo estimado (h)", f"{duracao_h:.2f}")

    frete_dict = {
        "Carreta": 7,
        "Carreta Trucada": 8,
        "Truck": 5,
        "Rodo-trem": 15,
        "Vanderleia": 11
    }
    frete = distancia_km * frete_dict.get(type_vehicle, 0)
    col3.metric("Valor frete (R$)", f"{frete:.2f}")

    # ---------------------------
    # Decodificar coordenadas da rota
    # ---------------------------
    geometry = rota["routes"][0]["geometry"]
    coords = convert.decode_polyline(geometry)["coordinates"]
    coords = [(lat, lon) for lon, lat in coords]

    # ---------------------------
    # Criar mapa e plotar rota
    # ---------------------------
    mapa = folium.Map(location=coords[0], zoom_start=10)
    folium.PolyLine(coords, color="blue", weight=5).add_to(mapa)
    folium.Marker(coords[0], tooltip="Origem").add_to(mapa)
    folium.Marker(coords[-1], tooltip="Destino").add_to(mapa)

    # ---------------------------
    # Plotar pedágios
    # ---------------------------
    pedagios_rota, total_pedagio = calcular_pedagios(coords)
    for p in pedagios_rota:
        folium.Marker(
            location=(p["lat"], p["lon"]),
            popup=f"{p['nome']} - {p['rodovia']} - R${p['valor']:.2f}",
            icon=folium.Icon(color="red", icon="road", prefix="fa")
        ).add_to(mapa)

    st_folium(mapa, center=True, use_container_width=True, height=500)
    st.metric("Valor total dos pedágios (R$)", f"{total_pedagio:.2f}")

# ---------------------------
# Executar app
# ---------------------------
Cargas()
