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
    

    df["Data"] = pd.to_datetime(df["Data"], errors="coerce")
    df["Turno"] = df["Turno"].astype(str).str.strip()

    # df = df.astype(str)
    return df