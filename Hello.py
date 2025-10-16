import streamlit as st
from database import conectData, fechamento
df = conectData()
df_fechamento = fechamento()


def main(): 
    st.set_page_config(
        page_title="Fechamento",
        page_icon="👋",
        layout="wide"
    )   
    
    data_default = [df["Data"].min(), df["Data"].max()]
    colaborador_default = "Todos"
    turno_default = "Todos os turnos"
    setor_default = "Expedição"

    with st.sidebar:
        if st.button("🔄 Resetar filtros"):
            st.session_state["setor"] = setor_default
            st.session_state["data"] = data_default
            st.session_state["colaborador"] = colaborador_default
            st.session_state["turno"] = turno_default
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
            ["Todos os turnos", "1°", "2°", "3°"],
            key="turnos"
        )

    st.markdown("# 👋 Fechamento Diário")  
    st.dataframe(df_fechamento)

if __name__ == "__main__":
    main()