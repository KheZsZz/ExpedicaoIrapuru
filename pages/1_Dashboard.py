import pandas as pd
import streamlit as st 
import plotly.express as px
from database import conectData, ocorrencias

st.set_page_config(page_title="Dashboard", page_icon="📈", layout="wide")

df = conectData()
df_ocorrencias = ocorrencias()

df["Data"] = pd.to_datetime(df["Data"], errors="coerce")
df_ocorrencias["Data"] = pd.to_datetime(df_ocorrencias["Data"], errors="coerce")

def dashboard():
    st.title("📊 Dashboard")

    # Valores default dos filtros
    data_default = [df["Data"].min(), df["Data"].max()]
    colaborador_default = "Todos"
    turno_default = "Todos os turnos"
    erro_default = "Todos"
    setor_default = "Expedição"

    # Sidebar
    with st.sidebar:
        st.subheader("🔍 Filtros")
        # Botão de reset
        if st.button("🔄 Resetar filtros"):
            st.session_state["setor"] = setor_default
            st.session_state["data"] = data_default
            st.session_state["colaborador"] = colaborador_default
            st.session_state["turno"] = turno_default
            st.session_state["erro"] = erro_default
            st.rerun()

        setor = st.selectbox('Setor', ('Expedição', 'Recebimento'), key="setor")
        data = st.date_input("Período", data_default, key="date")
        colaborador = st.selectbox(
            'Colaborador',
            ["Todos"] + sorted(df["Responsável"].dropna().unique()),
            key="colaborador"
        )
        turno = st.selectbox(
            'Turnos',
            ["Todos os turnos", *sorted(df["Turno"].dropna().unique())],
            key="turno"
        )
        erro_sel = st.selectbox(
            "Tipo de Erro",
            ["Todos"] + sorted(df_ocorrencias["Tipo de Erro"].dropna().unique()),
            key="erro"
        )

        

    # Garantir que data seja intervalo
    if isinstance(data, list) or isinstance(data, tuple):
        data_inicio, data_fim = pd.to_datetime(data[0]), pd.to_datetime(data[1])
    else:
        data_inicio, data_fim = pd.to_datetime(data), pd.to_datetime(data)

    if setor == "Expedição":
        df_filtrado = df[(df["Data"] >= data_inicio) & (df["Data"] <= data_fim)]
        df_filtrado_ocorrencias = df_ocorrencias[(df_ocorrencias["Data"] >= data_inicio) & (df_ocorrencias["Data"] <= data_fim)]

        # Aplicar filtro de turno
        if turno != "Todos os turnos":
            df_filtrado = df_filtrado[df_filtrado["Turno"] == turno]
            df_filtrado_ocorrencias = df_filtrado_ocorrencias[df_filtrado_ocorrencias["Turno"] == turno]

        # Aplicar filtro de colaborador
        if colaborador != "Todos":
            df_filtrado = df_filtrado[df_filtrado["Responsável"] == colaborador]
            df_filtrado_ocorrencias = df_filtrado_ocorrencias[df_filtrado_ocorrencias["Responsável correção"] == colaborador]

        if df_filtrado.empty:
            st.warning("Nenhum dado encontrado para os filtros selecionados.")
        else:
            # Métricas
            col1, col2, col3 = st.columns([3,1,3], vertical_alignment="center", gap="medium")
            with col2:
                cte_total = int(df_filtrado["Quantidade de CTe"].sum())
                cte_hoje = df_filtrado[df_filtrado["Data"].dt.date == data_inicio.date()]["Quantidade de CTe"].sum()
                st.metric(
                    label="CTEs emitidos",
                    value=cte_total,
                    delta=int(cte_hoje) if not pd.isna(cte_hoje) else 0
                )
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

            # Gráfico CTe por Responsável
            resumo = df_filtrado.groupby("Responsável")["Quantidade de CTe"].sum().reset_index()
            resumo = resumo.sort_values("Quantidade de CTe", ascending=False)
            fig = px.bar(
                resumo,
                x="Responsável",
                y="Quantidade de CTe",
                title=f"Quantidade de CTe por Responsável de {data_inicio.strftime('%d/%m/%Y')} a {data_fim.strftime('%d/%m/%Y')} - Turno: {turno} - Colaborador: {colaborador}",
                text="Quantidade de CTe"
            )
            st.plotly_chart(fig)

            # --- OCORRÊNCIAS ---
            st.title("🔢 Dashboard de Análise de Erros de CT-e")
            if erro_sel != "Todos":
                df_filtrado_ocorrencias = df_filtrado_ocorrencias[df_filtrado_ocorrencias["Tipo de Erro"] == erro_sel]

            col1, col2, col3 = st.columns(3)
            col1.metric("Total de Erros", len(df_filtrado_ocorrencias))
            col2.metric(
                "Erros Resolvidos",
                df_filtrado_ocorrencias[df_filtrado_ocorrencias["Status"].str.lower().str.contains("resolvido")].shape[0]
            )

            coluna_cliente = "Cliente (CNPJ)" if "Cliente (CNPJ)" in df_filtrado_ocorrencias.columns else "Cliente"
            col3.metric("Clientes Afetados", df_filtrado_ocorrencias[coluna_cliente].nunique())

            st.markdown("---")

            if not df_filtrado_ocorrencias.empty:
                df_tipo_erro = df_filtrado_ocorrencias["Tipo de Erro"].value_counts().reset_index()
                df_tipo_erro.columns = ["Tipo de Erro", "Qtde"]

                fig_tipo = px.funnel(df_tipo_erro, y="Tipo de Erro", x="Qtde", title="Erros por Tipo")
                st.plotly_chart(fig_tipo, use_container_width=True)

                fig_turno = px.pie(df_filtrado_ocorrencias, names="Turno", title="Distribuição de Erros por Turno")
                st.plotly_chart(fig_turno, use_container_width=True)

                erros_dia = df_filtrado_ocorrencias.groupby(df_filtrado_ocorrencias["Data"].dt.date).size().reset_index(name="Erros")
                fig_evolucao = px.line(erros_dia, x="Data", y="Erros", title="Evolução Diária de Erros")
                st.plotly_chart(fig_evolucao, use_container_width=True)

            st.markdown("### 🔢 Registros Filtrados")
            st.dataframe(df_filtrado_ocorrencias, use_container_width=True, hide_index=True)

    else:
        st.write("📦 Recebimento - em construção...")

if __name__ == "__main__":
    dashboard()
