import pandas as pd
import streamlit as st
import plotly.express as px
from database import ocorrencias

def painel_ocorrencia():
    # Configuração inicial
    df = ocorrencias()
    st.set_page_config(page_title="Dashboard CT-e", layout="wide")
    st.title("🔢 Dashboard de Análise de Erros de CT-e")

    # Filtros na barra lateral
    with st.sidebar:
        st.header("🔍 Filtros")
        data_range = st.date_input("Período", [df["Data"].min(), df["Data"].max()])
        turno_sel = st.selectbox("Turno", ["Todos"] + sorted(df["Turno"].dropna().unique()))
        erro_sel = st.selectbox("Tipo de Erro", ["Todos"] + sorted(df["Tipo de Erro"].dropna().unique())) 

    # Aplicar filtros
    df_filtrado = df[(df["Data"] >= pd.to_datetime(data_range[0])) & (df["Data"] <= pd.to_datetime(data_range[1]))]

    if turno_sel != "Todos":
        df_filtrado = df_filtrado[df_filtrado["Turno"] == turno_sel]

    if erro_sel != "Todos":
        df_filtrado = df_filtrado[df_filtrado["Tipo de Erro"] == erro_sel]

    # Métricas principais
    col1, col2, col3 = st.columns(3)
    col1.metric("Total de Erros", len(df_filtrado))
    col2.metric("Erros Resolvidos", df_filtrado[df_filtrado["Status"].str.lower().str.contains("resolvido")].shape[0])
    col3.metric("Clientes Afetados", df_filtrado["Cliente"].nunique())

    st.markdown("---")

    # Gráfico de Erros por Tipo
    df_tipo_erro = df_filtrado["Tipo de Erro"].value_counts().reset_index()
    df_tipo_erro.columns = ["Tipo de Erro", "Qtde"]

    fig_tipo = px.funnel(df_tipo_erro, y="Tipo de Erro", x="Qtde", title="Erros por Tipo")
    st.plotly_chart(fig_tipo, use_container_width=True)

    # Gráfico de Erros por Turno
    fig_turno = px.pie(df_filtrado, names="Turno", title="Distribuição de Erros por Turno")
    st.plotly_chart(fig_turno, use_container_width=True)

    # Evolução temporal dos erros
    erros_dia = df_filtrado.groupby(df_filtrado["Data"].dt.date).size().reset_index(name="Erros")
    fig_evolucao = px.line(erros_dia, x="Data", y="Erros", title="Evolução Diária de Erros")
    st.plotly_chart(fig_evolucao, use_container_width=True)


    # Tabela final
    st.markdown("### 🔢 Registros Filtrados")
    st.dataframe(df_filtrado, use_container_width=True, hide_index=True, selection_mode="multi-row")

painel_ocorrencia()