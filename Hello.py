import streamlit as st
import pandas as pd 
import os

def main(): 
    arquivo = "welcome.txt"

    st.set_page_config(
        page_title="Hello",
        page_icon="👋",
        layout="wide"
    )   

    st.markdown("# Olá👋")  
    col1, col2 = st.columns([4,2], gap="medium")
    
    if os.path.exists(arquivo):
        with open(arquivo, "r", encoding="utf-8") as f:
            conteudo_md = f.read()
        col1.markdown(conteudo_md, unsafe_allow_html=True)
        col2.markdown("> sites necessários", unsafe_allow_html=True)
    else: 

        st.write("Arquivo não encontrado... ")

if __name__ == "__main__":
    main()