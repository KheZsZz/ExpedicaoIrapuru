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

        # Filtros
        df_filtrado = df[
            (df["Data"] >= pd.to_datetime(data_inicial)) &
            (df["Data"] <= pd.to_datetime(data_final))
        ]
         
        if colaborador != "Todos":
            df_filtrado = df_filtrado[df_filtrado["Colaborador"] == colaborador]

        if tipo_operacao != "Todos":
            df_filtrado = df_filtrado[df_filtrado["Tipo"] == tipo_operacao]

        # Botão para enviar relatório ================================================
        if st.button("📊 Gerar e Enviar Relatório"):
            st.session_state["mostrar_form"] = True  # ativa o pop-up
            
        if st.session_state.get("mostrar_form", False):
            with st.form("form_email"):
                st.subheader("📬 Enviar relatório por e-mail")

                remetente = st.secrets["EMAIL_USER"]
                senha = st.secrets["EMAIL_PASS"]
                destinatario = st.secrets["EMAIL_CC"]


                enviar = st.form_submit_button("🚀 Enviar Agora")

                if enviar:
                    # Gera e envia relatório HTML interativo
                    enviar_relatorio_email(df_filtrado, remetente, senha, destinatario)
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
        label="💰 Abastecimento",
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
        dest_sum = (
            df_filtrado.groupby("Destino")["Total (min)"]
            .count()
            .sort_values(ascending=False)
            .head(10)
            .reset_index()
        )
        dest_sum.columns = ["Destino", "Quantidade"]
        fig = px.bar(
            dest_sum,
            x="Destino",
            y="Quantidade",
            text_auto=True,
            color="Destino",
            title="🏁 Destinos com Mais Operações",
        )
        st.plotly_chart(fig, use_container_width=True)

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


    # Cria o gráfico de pizza
    fig = px.pie(
        cte_por_colab,
        names="Colaborador",
        values="QTD de CT-e",
        title="📦 Percentual de CT-e Baixados por Colaborador",
        # hole=0.1  # tipo 'donut', se quiser pizza normal, remova
    )

    fig.update_traces(
        textinfo="percent+label+value",
        pull=[0.05 if i == 0 else 0 for i in range(len(cte_por_colab))],  # destaque leve no maior
    )

    fig.update_layout(
        title_x=0,
        showlegend=True
    )
    st.plotly_chart(fig, use_container_width=True)

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
