import pandas as pd
from datetime import datetime, timedelta

def conectData () :
    df = pd.read_csv("https://docs.google.com/spreadsheets/d/1d6dnzakl3ZXuQTyMzRAjugcL9g0mmw8r985PJj-IKA0/export?format=csv&gid=1435904190")
    df["Data"] = pd.to_datetime(df["Data"], errors="coerce", dayfirst=True)
    df["Quantidade de CTe"] = pd.to_numeric(df["Quantidade de CTe"], errors="coerce").astype("Int64")
    df = df.dropna(subset=["Data"])
    return df

def conhecimentos ():
    df = pd.read_csv(
        "https://docs.google.com/spreadsheets/d/1d6dnzakl3ZXuQTyMzRAjugcL9g0mmw8r985PJj-IKA0/export?format=csv&gid=2004182381", 
        dtype={
            "REMETENTE": str,
            "DESTINATARIO":str,
        }
    )
    return df

def ocorrencias():
    df = pd.read_csv(
        "https://docs.google.com/spreadsheets/d/1d6dnzakl3ZXuQTyMzRAjugcL9g0mmw8r985PJj-IKA0/export?format=csv&gid=0",
    )
    
    df['Data'] = pd.to_datetime(df["Data"], errors="coerce", dayfirst=True)
    df["Turno"] = df["Turno"].astype(str).str.strip()
    df = df.dropna(subset=["Data"])
    status_map = {
        "Resolvido": "✅ Resolvido",
        "Em analise": "⚠️ Em analise",
    }

    df["Status"] = df["Status"].apply(lambda x: status_map.get(x, x))

    return df

def desacordos():
    df = pd.read_csv(
        "https://docs.google.com/spreadsheets/d/1d6dnzakl3ZXuQTyMzRAjugcL9g0mmw8r985PJj-IKA0/export?format=csv&gid=1041434519",
    )
    df["Data"] = pd.to_datetime(df["Data"], errors="coerce", dayfirst=True)
    df = df.dropna(subset=["Data"])
    
    status_map = {
        "Finalizado": "✅ Finalizado",
        "Em andamento": "⚠️ Em análise",
    }

    df["Pendências"] = df["Pendências"].apply(lambda x: status_map.get(x, x))
    return df

def fechamento():
    df = pd.read_csv(
        "https://docs.google.com/spreadsheets/d/1EScFjmlwCXi212yQVz6b7sj-d7XniwlkR1lldTAQkRk/export?format=csv&gid=0",
        header=1 
    )
    
    df = df.dropna(subset=["Placa"])
    df = df.astype(str)
    df["Data"] = pd.to_datetime(df["Data"], errors="coerce", dayfirst=True)
    df['Total (min)'] = pd.to_timedelta(df['Total (min)'], errors='coerce').dt.total_seconds() / 60
    df['CT-e emitido'] = df['CT-e emitido'].astype(str).str.upper().isin(['TRUE', 'VERDADEIRO', '1'])
    df['Recepção de NFs'] = df['Recepção de NFs'].astype(str).str.upper().isin(['TRUE', 'VERDADEIRO', '1'])
    df['Pedágio'] = df['Pedágio'].astype(str).str.upper().isin(['TRUE', 'VERDADEIRO', '1'])
    return df

def ocorrenciasRecebimento():
    df = pd.read_csv(
        "https://docs.google.com/spreadsheets/d/1588Wscg2jZBDM6kQKsfjEeLeA8p3cU2qkpmHqhbw4mk/export?format=csv&gid=514085568",
        header=0
    )
    return df
