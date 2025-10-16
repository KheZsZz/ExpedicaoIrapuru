import pandas as pd

def conectData () :
    df = pd.read_csv("https://docs.google.com/spreadsheets/d/1d6dnzakl3ZXuQTyMzRAjugcL9g0mmw8r985PJj-IKA0/export?format=csv&gid=1435904190")
    df["Turno"] = df["Turno"].str.replace("°", "º").str.strip()

    df["Data"] = df["Data"].astype(str).str.replace(r"\D", "/", regex=True)
    df["Data"] = pd.to_datetime(df["Data"], dayfirst=True, errors="coerce")

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
        header=1,
        dtype={
            "Placa": str,
            "Destino": str,
            "Tipo": str,
            "Usuário": str,
            "OBS": str
        },
        # parse_dates=["Data "], 
        dayfirst=True, 
        # names= 1      
    )
    
    for col in ["inicio", "Finalização", "Total (min)"]:
        if col in df.columns:
            df[col] = pd.to_datetime(df[col], errors="coerce").dt.time

    bool_cols = ["CT-e emitido", "Recepção de NFs", "Pedágio"]
    for col in bool_cols:
        if col in df.columns:
            df[col] = df[col].astype(str).str.lower().isin(["true", "1", "sim", "yes"])
    
    
    df = df.dropna(subset=["Data"])

    return df

