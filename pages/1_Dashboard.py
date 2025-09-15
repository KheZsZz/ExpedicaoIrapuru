import pandas as pd
import streamlit as st 
import plotly.express as px
from database import conectData, ocorrencias, desacordos

st.set_page_config(page_title="Dashboard", page_icon="📈", layout="wide")

df = conectData()
df_ocorrencias = ocorrencias()
df_desacordos = desacordos()

df["Data"] = pd.to_datetime(df["Data"], errors="coerce")
df_ocorrencias["Data"] = pd.to_datetime(df_ocorrencias["Data"], errors="coerce")
df_desacordos["Data"] = pd.to_datetime(df_desacordos["Data"], errors="coerce")

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
            ["Todos os turnos", *sorted(df_ocorrencias["Turno"].dropna().unique())],
            key="turnos"
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
            df_filtrado_ocorrencias = df_filtrado_ocorrencias[df_filtrado_ocorrencias["Expedidor do Erro"] == colaborador]

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

def desacordos():
    st.title("❌ Dashboard de Desacordos / Ocorrências")

    data_default = [df_desacordos["Data"].min(), df_desacordos["Data"].max()]
    erro_default = "Todos"
    setor_default = "Todos"
    status_default = "Todos"

    with st.sidebar:
        st.subheader("🔍 Filtros Ocorrências")
        if st.button("🔄 Resetar filtros", key="reset_ocorrencias"):
            st.session_state["erro"] = erro_default
            st.session_state["data_oc"] = data_default
            st.session_state["setor_resp"] = setor_default
            st.session_state["status"] = status_default
            st.rerun()

        data = st.date_input("Período (Ocorrências)", data_default, key="date_oc")

        erro_sel = st.selectbox(
            "Tipo de Erro",
            ["Todos"] + sorted(df_desacordos["MOTIVO DA SUBSTITUIÇÃO"].dropna().unique()),
            key="erro"
        )

        setor_sel = st.selectbox(
            "Setor Responsável",
            ["Todos"] + sorted(df_desacordos["Setor Responsavel"].dropna().unique()),
            key="setor_resp"
        )

        status_sel = st.selectbox(
            "Status",
            ["Todos"] + sorted(df_desacordos["Status"].dropna().unique()),
            key="status"
        )

    # --- Filtragem de período ---
    if isinstance(data, (list, tuple)):
        data_inicio, data_fim = pd.to_datetime(data[0]), pd.to_datetime(data[1])
    else:
        data_inicio, data_fim = pd.to_datetime(data), pd.to_datetime(data)

    df_desacordos_filtrado = df_desacordos[
        (df_desacordos["Data"] >= data_inicio) &
        (df_desacordos["Data"] <= data_fim)
    ]

    # --- Aplicar filtros extras ---
    if erro_sel != "Todos":
        df_desacordos_filtrado = df_desacordos_filtrado[
            df_desacordos_filtrado["MOTIVO DA SUBSTITUIÇÃO"] == erro_sel
        ]

    if setor_sel != "Todos":
        df_desacordos_filtrado = df_desacordos_filtrado[
            df_desacordos_filtrado["Setor Responsavel"] == setor_sel
        ]

    if status_sel != "Todos":
        df_desacordos_filtrado = df_desacordos_filtrado[
            df_desacordos_filtrado["Status"] == status_sel
        ]

    # --- Dashboard ---
    if not df_desacordos_filtrado.empty:
        col1, col2, col3 = st.columns(3)
        col1.metric("Total de Erros", len(df_desacordos_filtrado))
        col2.metric("Finalizados", df_desacordos_filtrado[
            df_desacordos_filtrado["Status"].str.contains("Finalizado", case=False, na=False)
        ].shape[0])
        col3.metric("Clientes Afetados", df_desacordos_filtrado["Cliente"].nunique())

        st.markdown("---")

        # Motivos
        df_tipo_erro = df_desacordos_filtrado["MOTIVO DA SUBSTITUIÇÃO"].value_counts().reset_index()
        df_tipo_erro.columns = ["Tipo de Erro", "Qtde"]
        fig_tipo = px.bar(df_tipo_erro, y="Tipo de Erro", x="Qtde", orientation="h",
                          title="Erros por Tipo", text="Qtde")
        st.plotly_chart(fig_tipo, use_container_width=True)

        # Setor
        if "Setor Responsavel" in df_desacordos_filtrado.columns:
            fig_setor = px.pie(df_desacordos_filtrado, names="Setor Responsavel",
                               title="Erros por Setor Responsável")
            st.plotly_chart(fig_setor, use_container_width=True)

        # Evolução
        erros_dia = df_desacordos_filtrado.groupby(df_desacordos_filtrado["Data"].dt.date).size().reset_index(name="Erros")
        fig_evolucao = px.line(erros_dia, x="Data", y="Erros", title="Evolução Diária de Erros", markers=True)
        st.plotly_chart(fig_evolucao, use_container_width=True)

        # Ranking clientes
        top_clientes = df_desacordos_filtrado["Cliente"].value_counts().reset_index().head(5)
        top_clientes.columns = ["Cliente", "Ocorrências"]
        st.subheader("🏆 Top 5 Clientes com mais Ocorrências")
        st.dataframe(top_clientes, hide_index=True)

        # Ranking Expedidor
        if "Expedidor do Erro" in df_desacordos_filtrado.columns:
            ranking_expedidor = (
                df_desacordos_filtrado.groupby("Expedidor do Erro")
                .size()
                .reset_index(name="Qtde de Erros")
                .sort_values("Qtde de Erros", ascending=False)
            )
            if not ranking_expedidor.empty:
                st.markdown("### 🏆 Ranking de Erros por Expedidor")
                fig_expedidor = px.bar(
                    ranking_expedidor,
                    x="Qtde de Erros",
                    y="Expedidor do Erro",
                    orientation="h",
                    text="Qtde de Erros",
                    title="Ranking dos Erros por Expedidor",
                )
                fig_expedidor.update_layout(yaxis={'categoryorder': 'total ascending'})
                st.plotly_chart(fig_expedidor, use_container_width=True)

        st.markdown("### 📋 Registros Filtrados")
        st.dataframe(df_desacordos_filtrado, use_container_width=True, hide_index=True)

    else:
        st.info("Nenhuma ocorrência encontrada para os filtros aplicados.")


if __name__ == "__main__":
    aba = st.sidebar.radio("📂 Selecione o Dashboard", ["Emissão de CTe", "Desacordos"])
    if aba == "Emissão de CTe":
        dashboard()
    else:
        desacordos()
