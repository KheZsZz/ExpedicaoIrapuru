import pandas as pd
import streamlit as st 
import plotly.express as px
from database import conectData

dataframe = conectData()

# # Main page 
def dashboard():
    st.set_page_config(page_title="Dashboard", page_icon="📈", layout="wide")
    
    st.title("Dashboard")


    # Sidebar
    st.sidebar.title("Filtros")
    setor = st.sidebar.selectbox('Setore', ('Expedição', 'Recebimento'))
    data = st.sidebar.date_input( label="Data", format="DD/MM/YYYY", value="today" )
    turno = st.sidebar.selectbox('Turnos', ["Todos os turnos", *sorted(dataframe["Turno"].dropna().unique())])


    if setor == "Expedição":
        # itens necessários: Qtd total de Ctes emitidos, ranking Top 3 integrantes, top 1 turno, top 5 dias com mais Ctes emitidos
        
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
                    value = dataframe["Quantidade de CTe"].sum(),
                    delta= int(dataframe[dataframe["Data"].dt.date == data]["Quantidade de CTe"].sum())
                )

                
            # Ranking Top 3 integrantes
            with col3:
                st.caption("🔝 Top 3 responsáveis por CTe emitido")
                st.dataframe(
                        dataframe.groupby("Responsável")["Quantidade de CTe"]
                        .sum()
                        .reset_index()
                        .sort_values("Quantidade de CTe", ascending=False)
                        .head(3),
                        hide_index=True
                    )
            
            with col1:
                st.caption("📅 Top 3 dias com mais CTe emitidos")

                st.dataframe(
                    dataframe.groupby("Data")["Quantidade de CTe"]
                        .sum()
                        .nlargest(3)
                        .reset_index()
                        .sort_values("Quantidade de CTe", ascending=False),
                    hide_index=True
                )

        # Grafico   
        data = pd.to_datetime(data)
        if turno == "Todos os turnos":
            df_filtrado = dataframe[dataframe["Data"] == data]
        else:
            df_filtrado = dataframe[(dataframe["Data"] == data) & (dataframe["Turno"] == turno)]

        if df_filtrado.empty:
            st.warning("Nenhum dado encontrado para a data e turno selecionados.")
        else:
            resumo = df_filtrado.groupby("Responsável")["Quantidade de CTe"].sum().reset_index()
            resumo = resumo.sort_values("Quantidade de CTe", ascending=False)
            fig = px.bar(
                resumo,
                x="Responsável",
                y="Quantidade de CTe",
                title=f"Quantidade de CTe por Responsável em {data.strftime('%d/%m/%Y')} - Turno {turno}",
                text="Quantidade de CTe"
            )

            st.plotly_chart(fig)
    else:
        # Recebimento
        st.write("Em construção...")

if __name__ == "__main__":
    dashboard()