import requests
import streamlit as st 
import folium
from streamlit_folium import st_folium
from openrouteservice import convert

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

def fetch_api(remetente, destinatario):  
    coord_origem = get_coords(remetente)
    coord_destino = get_coords(destinatario)
    if not coord_origem or not coord_destino:
        return None

    ORS_API_KEY = "eyJvcmciOiI1YjNjZTM1OTc4NTExMTAwMDFjZjYyNDgiLCJpZCI6Ijc4NDkzZWRjZThhMTQ4NjZiMGUwNzMxNTA5MzI3Zjk3IiwiaCI6Im11cm11cjY0In0="  # Troque pela sua chave
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

def Cargas():
    st.set_page_config(page_title="Cargas", layout="wide")
    st.title("🚚 Frete Minimo")

    with st.container(horizontal_alignment="center"):
        col1, col2, col3 = st.columns([1,2,2], vertical_alignment="center", gap="medium")
        type_vehicle = col1.selectbox(
            label="🚗 Tipo de veículo:",
            placeholder="Escolha o tipo de veículo",
            options=("Carreta", "Carreta Trucada", "Truck", "Rodo-trem", "Vanderleia"),
            index=0,
            accept_new_options=True,
        )
        remetente = col2.text_input("🚩 Remetente:", value="Av. Miguel Pastuszak, 532")
        destinatario = col3.text_input("🚩 Destinatário:", value="R. Mansueto Bossardi, 375")

    rota = fetch_api(remetente, destinatario)

    # Mostrar distância e duração
    with st.container(vertical_alignment="center", horizontal_alignment="center", gap="medium"):
        col1, col2, col3 = st.columns(3, vertical_alignment="center", gap="medium")
        col1.metric(height="content", label="Distância (km)", value=f"{rota["routes"][0]["summary"]["distance"] / 1000:.2f} km")
        col2.metric("Tempo estimado (h)", f"{rota["routes"][0]["summary"]["duration"] / 3600:.2f} h")
        
        if type_vehicle == "Carreta":
            col3.metric("Valor frete:", f"R$ {(rota["routes"][0]["summary"]["distance"] / 1000) * 7:.2f}")
        elif type_vehicle == "Carreta Trucada":
            col3.metric("Valor frete:", f"R$ {(rota["routes"][0]["summary"]["distance"] / 1000) * 8:.2f}")
        elif type_vehicle == "Truck":
            col3.metric("Valor frete:", f"R$ {(rota["routes"][0]["summary"]["distance"] / 1000) * 5:.2f}")
        elif type_vehicle == "Rodo-trem":
            col3.metric("Valor frete:", f"R$ {(rota["routes"][0]["summary"]["distance"] / 1000) * 15:.2f}")
        elif type_vehicle == "Vanderleia":
            col3.metric("Valor frete:", f"R$ {(rota["routes"][0]["summary"]["distance"] / 1000) * 11:.2f}")


    if not rota or "routes" not in rota:
        st.error("Não foi possível obter a rota.")
        return

    # Decodificar geometria para coordenadas (lat, lon)
    geometry = rota["routes"][0]["geometry"]
    coords = convert.decode_polyline(geometry)["coordinates"]
    coords = [(lat, lon) for lon, lat in coords]  # Inverter ordem

    # Criar mapa
    mapa = folium.Map(location=coords[0], zoom_start=10)
    folium.PolyLine(coords, color="blue", weight=5).add_to(mapa)
    folium.Marker(coords[0], tooltip="Origem").add_to(mapa)
    folium.Marker(coords[-1], tooltip="Destino").add_to(mapa)

    # Mostrar mapa
    st_folium(mapa, center=True, use_container_width=True, height=500)

Cargas()
