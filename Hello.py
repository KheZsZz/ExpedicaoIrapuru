import streamlit as st
import pandas as pd
from database import fechamento
from relatorios import enviar_relatorio_email

import plotly.express as px

df = fechamento()

def main(): 
    st.set_page_config(
        page_title="Fechamento",
        page_icon="👋",
        layout="wide"
    )   
    
    st.title("📊 Fechamento Operacional")
    
 # ============================= Filtros =======================================
    with st.sidebar:
        data_inicial, data_final = st.date_input(
            "📅 Período",
            value=[df["Data"].max(), df["Data"].max()],
            min_value=df["Data"].min(),
            max_value=df["Data"].max()
        )

        colaborador = st.selectbox(
            "👷 Colaborador",
            options=["Todos", *sorted(df["Colaborador"].dropna().unique().tolist())]
        )

        tipo_operacao = st.selectbox(
            "⚙️ Tipo de Operação",
            options=["Todos", *sorted(df["Tipo"].dropna().unique().tolist())]
        )
       
        df_filtrado = df[
            (df["Data"] >= pd.to_datetime(data_inicial)) &
            (df["Data"] <= pd.to_datetime(data_final))
        ]
         
        if colaborador != "Todos":
            df_filtrado = df_filtrado[df_filtrado["Colaborador"] == colaborador]

        if tipo_operacao != "Todos":
            df_filtrado = df_filtrado[df_filtrado["Tipo"] == tipo_operacao]

        # Botão para enviar relatório
        if st.button("📊 Gerar e Enviar Relatório"):
            st.session_state["mostrar_form"] = True  # ativa o pop-up
            
        if st.session_state.get("mostrar_form", False):
            with st.form("form_email"):
                st.subheader("📬 Enviar relatório por e-mail")

                remetente = st.secrets["EMAIL_USER"]
                senha = st.secrets["EMAIL_PASS"]
                destinatario = st.secrets["EMAIL_CC"]
                ocorrencias = st.text_area("📝 Ocorrências adicionais (opcional)", "")
                turno = st.selectbox(
                    "⏰ Selecionar Turno",
                    options=["1º", "2º", "3º"]
                )

                enviar = st.form_submit_button("🚀 Enviar Agora")

                if enviar:
                    # Gera e envia relatório HTML interativo
                    enviar_relatorio_email(df_filtrado, remetente, senha, destinatario, ocorrencias, turno)
                    st.success("✅ Relatório enviado com sucesso!")
                    st.session_state["mostrar_form"] = False

    # ==================== Cabeçalho ====================
    col1, col2, col3 = st.columns(3)
    
    lancamentos = df_filtrado[df_filtrado['Tipo'] == "Lançamento"]
    col1.metric(
        label="📦 Total de Operações",
        value=f"{lancamentos.shape[0]:,.0f}",
        delta=f"{(lancamentos.shape[0] / df_filtrado.shape[0] * 100):.1f}%" if df_filtrado.shape[0] > 0 else "0%"
    )
    
    abastecimentos = df_filtrado[df_filtrado['Tipo'] == "Abastecimento"]
    col2.metric(
        label="⛽ Abastecimento",
        value=f"{abastecimentos.shape[0]:,.0f}",
        delta=f"{(abastecimentos.shape[0] / df_filtrado.shape[0] * 100):.1f}%" if df_filtrado.shape[0] > 0 else "0%"
    )

    col3.metric(
        label="💰 Pedágio",
        value=f"{df_filtrado[df_filtrado['Pedágio'] == True].shape[0]:,.0f}",
        delta=f"{(df_filtrado['Pedágio'].mean()*100 if df_filtrado.shape[0] > 0 else 0):.1f}%"
    )

    # ==================== Gráficos ====================
    st.subheader("🧮 Visão Geral das Operações")
    aba1, aba2 = st.tabs(["Quantidade por Operação", "Quantidade por Destino"])

    with aba1:
        tipo_sum = (
            df_filtrado.groupby("Tipo")["Total (min)"]
            .count()
            .sort_values(ascending=False)
            .reset_index()
        )
        tipo_sum.columns = ["Tipo de Operação", "Quantidade"]
        fig = px.bar(
            tipo_sum,
            x="Tipo de Operação",
            y="Quantidade",
            text_auto=True,
            title="📊 Quantidade de Operações por Tipo",
            color="Tipo de Operação",
        )
        st.plotly_chart(fig, use_container_width=True)

    with aba2:
        # Filtra apenas lançamentos (com lowercase)
        df_lanc = df_filtrado[df_filtrado["Tipo"].str.lower() == "lançamento"]

        # Agrupa e conta por destino
        dest_sum = (
            df_lanc.groupby("Destino")["Total (min)"]
            .count()
            .sort_values(ascending=False)
            .head(10)
            .reset_index()
        )

        dest_sum.columns = ["Destino", "Quantidade"]

        # Cria o gráfico
        fig = px.bar(
            dest_sum,
            x="Destino",
            y="Quantidade",
            text_auto=True,
            color="Destino",
            title="🏁 Destinos com Mais Lançamentos de Viagem",
        )

        # Personalizações visuais
        fig.update_layout(
            xaxis_title="Destino",
            yaxis_title="Quantidade de Lançamentos",
            title_x=0,
            showlegend=True,
            plot_bgcolor="rgba(0,0,0,0)",
            paper_bgcolor="rgba(0,0,0,0)",
        )

        fig.update_traces(textposition="outside")

        # Exibe o gráfico
        st.plotly_chart(fig, use_container_width=True)

        # Exibe a tabela abaixo para referência
        # st.dataframe(dest_sum, use_container_width=True, hide_index=True)

    # ==================== Detalhamento ====================
    st.subheader("📋 Detalhamento das Operações")
    df_baixa = df_filtrado[df_filtrado["Tipo"].str.lower() == "baixa"]
    df_baixa["QTD de CT-e"] = pd.to_numeric(df_baixa["QTD de CT-e"], errors="coerce").fillna(0)
    cte_por_colab = (
        df_baixa.groupby("Colaborador")["QTD de CT-e"]
        .sum()
        .reset_index()
        .sort_values("QTD de CT-e", ascending=False)
    )

    aba3, aba4, aba5 = st.tabs([
        "Percentual de baixa",
        "Percentual de abastecimento",
        "Percentual de lançamento de viagem"
    ])

    # ======== ABA 3 - BAIXAS ========
    with aba3:

        if not df_baixa.empty:
            cte_por_colab = df_baixa.groupby("Colaborador", as_index=False)["QTD de CT-e"].sum()

            fig = px.pie(
                cte_por_colab,
                names="Colaborador",
                values="QTD de CT-e",
                title="📦 Percentual de CT-e Baixados por Colaborador",
            )

            fig.update_traces(
                textinfo="percent+label+value",
                pull=[0.05 if i == cte_por_colab["QTD de CT-e"].idxmax() else 0 for i in range(len(cte_por_colab))]
            )

            fig.update_layout(title_x=0, showlegend=True)
            st.plotly_chart(fig, use_container_width=True)
        else:
            st.warning("⚠️ Nenhum dado de baixa encontrado.")


    with aba4:
        # Corrige o filtro (tudo minúsculo)
        df_abast = df_filtrado[df_filtrado["Tipo"].str.lower() == "abastecimento"]

        if not df_abast.empty:
            # Agrupa por colaborador e conta quantas placas (ou abastecimentos) fez
            abast_por_colab = df_abast.groupby("Colaborador", as_index=False)["Placa"].count()
            abast_por_colab.rename(columns={"Placa": "Qtd Abastecimentos"}, inplace=True)

            # Gera o gráfico de pizza
            fig2 = px.pie(
                abast_por_colab,
                names="Colaborador",
                values="Qtd Abastecimentos",
                title="⛽ Percentual de Abastecimentos por Colaborador",
            )

            # Destaca o colaborador com mais abastecimentos
            fig2.update_traces(
                textinfo="percent+label+value",
                pull=[0.05 if i == abast_por_colab["Qtd Abastecimentos"].idxmax() else 0 for i in range(len(abast_por_colab))]
            )

            fig2.update_layout(title_x=0, showlegend=True)
            st.plotly_chart(fig2, use_container_width=True)

            # Mostra os dados abaixo do gráfico
            # st.dataframe(abast_por_colab, use_container_width=True, hide_index=True)

        else:
            st.warning("⚠️ Nenhum dado de abastecimento encontrado.")

    with aba5:
        # Corrigir o filtro (minúsculo)
        df_lanc = df_filtrado[df_filtrado["Tipo"].str.lower() == "lançamento"]

        if not df_lanc.empty:
            # Agrupa por colaborador e conta quantos lançamentos
            lanc_por_colab = df_lanc.groupby("Colaborador", as_index=False)["Placa"].count()
            lanc_por_colab.rename(columns={"Placa": "Qtd Lançamentos"}, inplace=True)

            # Gráfico de pizza
            fig3 = px.pie(
                lanc_por_colab,
                names="Colaborador",
                values="Qtd Lançamentos",
                title="🚛 Percentual de Lançamentos de Viagem por Colaborador",
            )

            # Configura exibição e destaque
            fig3.update_traces(
                textinfo="percent+label+value",
                pull=[0.05 if i == lanc_por_colab["Qtd Lançamentos"].idxmax() else 0 for i in range(len(lanc_por_colab))],
                texttemplate="%{label}<br>%{percent:.1%}<br>%{value}"
            )

            fig3.update_layout(title_x=0, showlegend=True)
            st.plotly_chart(fig3, use_container_width=True)

            # Mostra os dados em tabela
            # st.dataframe(lanc_por_colab, use_container_width=True, hide_index=True)

        else:
            st.warning("⚠️ Nenhum dado de lançamento encontrado.")
    # ==================== Insights ====================
    st.subheader("💡 Insights Automáticos")
    aba3, aba4 = st.tabs(["Tempo médio por operação", "Tempo médio ocioso por colaborador"])

    with aba3:
        tempo_medio = (
            df_filtrado.groupby("Tipo")["Total (min)"]
            .mean()
            .reset_index()
            .sort_values("Total (min)", ascending=False)
        )
        tempo_medio["Total (min)"] = tempo_medio["Total (min)"].round(1)
        fig = px.bar(
            tempo_medio,
            x="Tipo",
            y="Total (min)",
            text_auto=".1f",
            title="Tempo médio por tipo de operação (em minutos)",
            color="Tipo"
        )
        st.plotly_chart(fig, use_container_width=True)
        
    with aba4:  
        TEMPO_ESPERADO_H = 7
        tempo_trabalhado = (
            df_filtrado.groupby(["Colaborador", "Data"])["Total (min)"]
            .sum()
            .reset_index()
            .rename(columns={"Total (min)": "Tempo trabalhado (min)"})
        )
        tempo_trabalhado["Tempo trabalhado (h)"] = tempo_trabalhado["Tempo trabalhado (min)"] / 60
        tempo_trabalhado["Tempo ocioso (h)"] = TEMPO_ESPERADO_H - tempo_trabalhado["Tempo trabalhado (h)"]
        tempo_trabalhado["Tempo ocioso (h)"] = tempo_trabalhado["Tempo ocioso (h)"].clip(lower=0)
        tempo_trabalhado["% Ociosidade"] = (tempo_trabalhado["Tempo ocioso (h)"] / TEMPO_ESPERADO_H * 100).round(1)

        fig = px.bar(
            tempo_trabalhado,
            x="Colaborador",
            y="Tempo ocioso (h)",
            text_auto=".2f",
            color="Colaborador",
            title="Tempo Ocioso (em horas, diferença das 8h previstas)"
        )
        st.plotly_chart(fig, use_container_width=True)

    # ==================== Alertas ====================
    if df['CT-e emitido'].mean() < 0.7:
        st.warning("⚠️ Menos de 70% das operações tiveram CT-e emitido.")
    else:
        st.success("✅ Alta conformidade de emissão de CT-e.")

    if df['Pedágio'].mean() > 0.5:
        st.info("💰 Mais da metade das viagens teve pedágio registrado.")

if __name__ == "__main__":
    main()
