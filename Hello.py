import streamlit as st
import pandas as pd 

def main():
    st.set_page_config(
        page_title="Hello",
        page_icon="👋",
    )
    st.sidebar.success("dados carregados...")

    st.write("# Welcome👋")

if __name__ == "__main__":
    main()