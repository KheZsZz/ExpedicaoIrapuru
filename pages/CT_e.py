import pandas as pd
import streamlit as st 
import re
import httpx
import asyncio
import time

from database import conhecimentos

df = conhecimentos()

# Função para limpar o CNPJ
def limpar_cnpj(cnpj):
    return re.sub(r'\D', '', cnpj)

# Função para consultar razão social
async def consultar_razao_social(cnpj):
    cnpj = limpar_cnpj(cnpj)
    if len(cnpj) != 14:
        return "CNPJ inválido"

    url = f"https://www.receitaws.com.br/v1/cnpj/{cnpj}"
    try:
        async with httpx.AsyncClient(timeout=10) as client:
            resposta = await client.get(url)

        if resposta.status_code != 200 or not resposta.text.strip():
            return "Erro: resposta vazia ou inválida"

        try:
            dados = resposta.json()
        except ValueError:
            return "Erro ao decodificar JSON"

        if dados.get("status") == "ERROR":
            return dados.get("message", "Erro na consulta")

        return dados.get("nome", "Razão social não encontrada")

    except httpx.RequestError as e:
        return f"Erro de rede: {e}"

st.set_page_config(page_title="Conhecimentos", page_icon="💵")
st.set_page_config(layout="wide")
st.title("CT-e")    

with st.container(border=True, key="consulta"):
    col1, col2 = st.columns([5,1], vertical_alignment="bottom", gap="large")
    cnpj_input = col1.text_input("Digite o CNPJ (com ou sem formatação):", placeholder="00.000.000/0000-00")
    if col2.button("Consultar"):
        with st.spinner("Consultando..."):
            resultado = consultar_razao_social(cnpj_input)
            if resultado == "CNPJ inválido":
                st.warning(resultado)
            else:
                if not resultado: 
                    st.error("CNPJ não encontrado!")

filtro = df[(df["REMETENTE"] == limpar_cnpj(cnpj_input)) | (df["DESTINATARIO"] == limpar_cnpj(cnpj_input))]

if not filtro.empty:
    with st.spinner("Consultando..."):
        for index, row in filtro.iterrows():
            st.success(f"{asyncio.run(consultar_razao_social(row['DESTINATARIO']))} X {asyncio.run(consultar_razao_social(row['REMETENTE']))}")
            
            with st.container(border=True):
                st.image(f"./public/image/{row['UNIDADE']}.svg", caption="Unidade")
                col1, col2 = st.columns([1,3], vertical_alignment="top", gap="small")
                with col1:
                    st.markdown("**Frete conta:**")
                    st.markdown("**Tipo de frete:**")
                    st.markdown("**Tipo de carga:**")
                    st.markdown("**Tipo de veículo:**")
                    st.markdown("**OBS:**")

                with col2:
                    
                    st.write(row["FRETE CONTA"])
                    st.write(row["TIPO DE FRETE"])
                    st.write(row["TIPO DE CARGA"])
                    st.write(row["TIPO DE VEICULO"])
                    st.write(row["OBSERVAÇOES CTE"])

            col1, col2 = st.columns([5,2], vertical_alignment="top", gap="small")

            col1.markdown("## Passo a passo:")
            linhas = row["PASSO A PSSO DE EMISSÃO"].split(";") 
            for linha in linhas:
                col1.markdown(f'{linha}')

            col2.markdown(f">Obs: {row['OBSERVAÇOES FINANCEIRAS']}")
            

else :
    st.warning("dados não encontrado...")
# st.dataframe(df["DESTINATARIO"])