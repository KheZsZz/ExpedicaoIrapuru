import streamlit as st
import pandas as pd
from database import conectData, fechamento
# df = conectData()
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
            value = [df["Data"].max(), df["Data"].max()],
            min_value = df["Data"].min(),
            max_value = df["Data"].max()
        )

        colaborador = st.selectbox(
            "👷 Colaborador",
            options = ["Todos", *sorted(df["Colaborador"].dropna().unique().tolist())]

        )

        tipo_operacao = st.selectbox(
            "⚙️ Tipo de Operação",
            options=["Todos",*sorted(df["Tipo"].dropna().unique().tolist())]
        )
        
    # Filtros ============
    df_filtrado = df[
        (df["Data"] >= pd.to_datetime(data_inicial)) &
        (df["Data"] <= pd.to_datetime(data_final))
    ]

    if colaborador != "Todos":
        df_filtrado = df_filtrado[df_filtrado["Colaborador"] == colaborador]

    if tipo_operacao != "Todos":
        df_filtrado = df_filtrado[df_filtrado["Tipo"] == tipo_operacao]
    
    
    col1, col2, col3 = st.columns(3)

    # col1.metric("⏱ Tempo Total (min)", f"{df_filtrado['Total (min)'].sum():,.0f} min")
    lancamentos = df_filtrado[df_filtrado['Tipo'] == "Lançamento"]
    col1.metric(
        label= "📦 Total de Operações",
        value=f"{lancamentos.shape[0]:,.0f}",
        delta=f"{(lancamentos.shape[0] / df_filtrado.shape[0] * 100):.1f}%"
    )
    
    abastecimentos = df_filtrado[df_filtrado['Tipo'] == "Abastecimento"]
    col2.metric(
        label="💰 Abastecimento",
        value=f"{abastecimentos.shape[0]:,.0f}",
        delta=f"{(abastecimentos.shape[0] / df_filtrado.shape[0] * 100):.1f}%"
    )

    col3.metric(
        label="💰 Pedágio",
        value=f"{df_filtrado[df_filtrado['Pedágio'] == True].shape[0]:,.0f}",
        delta=f"{df_filtrado['Pedágio'].mean()*100:.1f}%"
    )


    st.subheader("🧮 Visão Geral das Operações")
    aba1, aba2 = st.tabs(["Por Operação", "Por Destino"])

    with aba1:
        tipo_sum = df_filtrado.groupby("Tipo")["Total (min)"].count().sort_values(ascending=False)
        st.line_chart(tipo_sum, use_container_width=True)

    with aba2:
        dest_sum = df_filtrado.groupby("Destino")["Total (min)"].count().sort_values(ascending=False).head(10)
        st.line_chart(dest_sum, use_container_width=True)

    st.subheader("📋 Detalhamento das Operações")
    st.dataframe(
        df_filtrado[[
            "Data", "Placa", "Tipo", "Destino", "Total (min)",
            "CT-e emitido", "Recepção de NFs", "Pedágio", "Colaborador"
        ]],
        use_container_width=True,
        hide_index=True
    )
    
    st.subheader("💡 Insights Automáticos")

    mais_lento = df.loc[df['Total (min)'].idxmax()] if len(df) > 0 else None
    if mais_lento is not None:
        st.markdown(f"""
        - 🚛 **Placa com maior operação:** `{mais_lento['Placa']}` com **{mais_lento['Total (min)']:.0f} min**
        - 🏙️ **Destino:** {mais_lento['Destino']}
        - 📅 **Data:** {mais_lento['Data'].strftime('%d/%m/%Y')}
        """)

    if df['CT-e emitido'].mean() < 0.7:
        st.warning("⚠️ Menos de 70% das operações tiveram CT-e emitido.")
    else:
        st.success("✅ Alta conformidade de emissão de CT-e.")

    if df['Pedágio'].mean() > 0.5:
        st.info("💰 Mais da metade das viagens teve pedágio registrado.")

if __name__ == "__main__":
    main()