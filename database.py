import pandas as pd
from datetime import datetime, timedelta

def conectData () :
    df = pd.read_csv("https://docs.google.com/spreadsheets/d/1d6dnzakl3ZXuQTyMzRAjugcL9g0mmw8r985PJj-IKA0/export?format=csv&gid=1435904190")
    df["Turno"] = df["Turno"].str.replace("°", "º").str.strip()

    df["Data"] = df["Data"].astype(str).str.replace(r"\D", "/", regex=True)
    df["Data"] = pd.to_datetime(df["Data"], errors="coerce", dayfirst=True)

    df["Quantidade de CTe"] = pd.to_numeric(df["Quantidade de CTe"], errors="coerce").astype("Int64")

    return df

def conhecimentos ():
    df = pd.read_csv(
        "https://docs.google.com/spreadsheets/d/1d6dnzakl3ZXuQTyMzRAjugcL9g0mmw8r985PJj-IKA0/export?format=csv&gid=2004182381", 
        dtype={
            "REMETENTE": str,
            "DESTINATARIO":str,
        }
    )

    df = df.astype(str)

    return df

def ocorrencias():
    df = pd.read_csv(
        "https://docs.google.com/spreadsheets/d/1d6dnzakl3ZXuQTyMzRAjugcL9g0mmw8r985PJj-IKA0/export?format=csv&gid=0",
    )
    
    df['Data'] = pd.to_datetime(df['Data'], errors='coerce')  # Garante que a coluna seja datetime
    df['Data'] = df['Data'].dt.strftime('%d/%m/%Y')
    
    df["Turno"] = df["Turno"].astype(str).str.strip()

    # df = df.astype(str)
    return df

def desacordos():
    
    df = pd.read_csv(
        "https://docs.google.com/spreadsheets/d/1d6dnzakl3ZXuQTyMzRAjugcL9g0mmw8r985PJj-IKA0/export?format=csv&gid=1041434519",
    )
    
    df['Data'] = pd.to_datetime(df['Data'], errors='coerce')  # Garante que a coluna seja datetime
    df['Data'] = df['Data'].dt.strftime('%d/%m/%Y')
    
    # df["Turno"] = df["Turno"].astype(str).str.strip()

    # df = df.astype(str)
    return df

def fechamento():
    df = pd.read_csv(
        "https://docs.google.com/spreadsheets/d/1EScFjmlwCXi212yQVz6b7sj-d7XniwlkR1lldTAQkRk/export?format=csv&gid=0",
        header=1 )
    df = df.dropna(subset=["Data"])
    df = df.astype(str)
    
    df["Data"] = pd.to_datetime(df["Data"], errors="coerce", dayfirst=True)
    df['Total (min)'] = pd.to_timedelta(df['Total (min)'], errors='coerce').dt.total_seconds() / 60
    df['CT-e emitido'] = df['CT-e emitido'].astype(str).str.upper().isin(['TRUE', 'VERDADEIRO', '1'])
    df['Recepção de NFs'] = df['Recepção de NFs'].astype(str).str.upper().isin(['TRUE', 'VERDADEIRO', '1'])
    df['Pedágio'] = df['Pedágio'].astype(str).str.upper().isin(['TRUE', 'VERDADEIRO', '1'])
        
    
    return df

