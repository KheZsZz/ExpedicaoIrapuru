import pandas as pd
import streamlit as st 
import plotly.express as px
from database import conectData
from database import ocorrencias

df = conectData()
df_ocorrencias = ocorrencias()

df["Data"] = pd.to_datetime(df["Data"], errors="coerce")  # Converte e força erro em valores inválidos
df_ocorrencias["Data"] = pd.to_datetime(df_ocorrencias["Data"], errors="coerce")  # Converte e força erro em valores inválidos

# # Main page 
def dashboard():
    st.set_page_config(page_title="Dashboard", page_icon="📈", layout="wide")
    st.title("Dashboard")

    # Sidebar
    with st.sidebar:
        setor = st.selectbox('Setore', ('Expedição', 'Recebimento'))
        data = st.date_input("Período", [df["Data"].min(), df["Data"].max()])
        turno = st.selectbox('Turnos', ["Todos os turnos", *sorted(df["Turno"].dropna().unique())])
        erro_sel = st.selectbox("Tipo de Erro", ["Todos"] + sorted(df_ocorrencias["Tipo de Erro"].dropna().unique())) 



    if setor == "Expedição":
        # itens necessários: Qtd total de Ctes emitidos, ranking Top 3 integrantes, top 1 turno, top 5 dias com mais Ctes emitidos
        df_filtrado = df[(df["Data"] >= pd.to_datetime(data[0])) & (df["Data"] <= pd.to_datetime(data[1]))]
        df_filtrado_ocorrencias = df_ocorrencias[(df_ocorrencias["Data"] >= pd.to_datetime(data[0])) & (df_ocorrencias["Data"] <= pd.to_datetime(data[1]))]

        with st.container(border=True):
            col1, col2, col3 = st.columns([3,1,3],vertical_alignment="center", gap="medium")
            # Qtd total de CTEs emitidos
            with col2:
                st.metric(
                    label="CTEs emitidos", 
                    label_visibility="visible",
                    border=False,
                    help="",
                    width = "content",
                    value = df_filtrado["Quantidade de CTe"].sum(),
                    delta= int(df_filtrado[df_filtrado["Data"].dt.date == data]["Quantidade de CTe"].sum())
                )

                
            # Ranking Top 3 integrantes
            with col3:
                st.caption("🔝 Top 3 responsáveis por CTe emitido")
                st.dataframe(
                        df_filtrado.groupby("Responsável")["Quantidade de CTe"]
                        .sum()
                        .reset_index()
                        .sort_values("Quantidade de CTe", ascending=False)
                        .head(3),
                        hide_index=True
                    )
            
            with col1:
                st.caption("📅 Top 3 dias com mais CTe emitidos")

                st.dataframe(
                    df_filtrado.groupby("Data")["Quantidade de CTe"]
                        .sum()
                        .nlargest(3)
                        .reset_index()
                        .sort_values("Quantidade de CTe", ascending=False),
                    hide_index=True
                )

        # Grafico   
        data = pd.to_datetime(data)
        if turno == "Todos os turnos":
            df_filtrado = df_filtrado[(df_filtrado["Data"] >= pd.to_datetime(data[0])) & (df_filtrado["Data"] <= pd.to_datetime(data[1]))]
            df_filtrado_ocorrencias = df_filtrado_ocorrencias[(df_filtrado_ocorrencias["Data"] >= pd.to_datetime(data[0])) & (df_filtrado_ocorrencias["Data"] <= pd.to_datetime(data[1]))]
        else:
            df_filtrado = df_filtrado[(df_filtrado["Data"] >= pd.to_datetime(data[0])) & (df_filtrado["Data"] <= pd.to_datetime(data[1])) & (df_filtrado["Turno"] == turno)]
            df_filtrado_ocorrencias = df_filtrado_ocorrencias[(df_filtrado_ocorrencias["Data"] >= pd.to_datetime(data[0])) & (df_filtrado_ocorrencias["Data"] <= pd.to_datetime(data[1])) & (df_filtrado_ocorrencias["Turno"] == turno)]
        if df_filtrado.empty:
            st.warning("Nenhum dado encontrado para a data e turno selecionados.")
        else:
            resumo = df_filtrado.groupby("Responsável")["Quantidade de CTe"].sum().reset_index()
            resumo = resumo.sort_values("Quantidade de CTe", ascending=False)
            fig = px.bar(
                resumo,
                x="Responsável",
                y="Quantidade de CTe",
                title=f"Quantidade de CTe por Responsável de {data[0].strftime('%d/%m/%Y')} a {data[1].strftime('%d/%m/%Y')} - Turno: {turno}",
                text="Quantidade de CTe"
            )

            st.plotly_chart(fig)




            # OCORRENCIAS

            st.title("🔢 Dashboard de Análise de Erros de CT-e")
            if erro_sel != "Todos":
                df_filtrado_ocorrencias = df_filtrado_ocorrencias[df_filtrado_ocorrencias["Tipo de Erro"] == erro_sel]

            # Métricas principais
            # st.dataframe(df_filtrado)
            col1, col2, col3 = st.columns(3)
            col1.metric("Total de Erros", len(df_filtrado_ocorrencias))
            col2.metric("Erros Resolvidos", df_filtrado_ocorrencias[df_filtrado_ocorrencias["Status"].str.lower().str.contains("Resolvido")].shape[0])
            col3.metric("Clientes Afetados", df_filtrado_ocorrencias["Cliente (CNPJ)"].nunique())

            st.markdown("---")

            # Gráfico de Erros por Tipo
            df_tipo_erro = df_filtrado_ocorrencias["Tipo de Erro"].value_counts().reset_index()
            df_tipo_erro.columns = ["Tipo de Erro", "Qtde"]

            fig_tipo = px.funnel(df_tipo_erro, y="Tipo de Erro", x="Qtde", title="Erros por Tipo")
            st.plotly_chart(fig_tipo, use_container_width=True)

            # Gráfico de Erros por Turno
            fig_turno = px.pie(df_filtrado_ocorrencias, names="Turno", title="Distribuição de Erros por Turno")
            st.plotly_chart(fig_turno, use_container_width=True)

            # Evolução temporal dos erros
            erros_dia = df_filtrado_ocorrencias.groupby(df_filtrado_ocorrencias["Data"].dt.date).size().reset_index(name="Erros")
            fig_evolucao = px.line(erros_dia, x="Data", y="Erros", title="Evolução Diária de Erros")
            st.plotly_chart(fig_evolucao, use_container_width=True)


            # Tabela final
            st.markdown("### 🔢 Registros Filtrados")
            st.dataframe(df_filtrado_ocorrencias, use_container_width=True, hide_index=True, selection_mode="multi-row")

    else:
        # Recebimento
        st.write("Em construção...")

if __name__ == "__main__":
    dashboard()