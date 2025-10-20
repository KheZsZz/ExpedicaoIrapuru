from datetime import datetime
import plotly.express as px
import plotly.io as pio
import io
from PIL import Image
import smtplib
from email.mime.multipart import MIMEMultipart
from email.mime.text import MIMEText
from email.mime.image import MIMEImage
import pandas as pd

# -----------------------------
# Função para gerar gráficos e retornar imagens em memória
# -----------------------------
def gerar_graficos(df):
    imagens = []

    # Gráfico 1 - CT-e por colaborador
    df_baixa = df[df["Tipo"].str.lower() == "baixa"]
    df_baixa["QTD de CT-e"] = pd.to_numeric(df_baixa["QTD de CT-e"], errors="coerce").fillna(0)
    cte_por_colab = (
        df_baixa.groupby("Colaborador")["QTD de CT-e"]
        .sum()
        .reset_index()
        .sort_values("QTD de CT-e", ascending=False)
    )

    fig1 = px.pie(
        cte_por_colab,
        names="Colaborador",
        values="QTD de CT-e",
        title="Distribuição de CT-e por Colaborador",
        hole=0.4,
        color="Colaborador"
    )
    img_bytes1 = fig1.to_image(format="png")
    imagens.append(img_bytes1)

    # Gráfico 2 - Tempo médio por tipo
    tempo_tipo = df.groupby("Tipo")["Total (min)"].mean().reset_index()
    fig2 = px.bar(
        tempo_tipo,
        x="Tipo",
        y="Total (min)",
        title="Tempo Médio por Tipo de Operação (min)",
        text_auto=".1f",
        color="Tipo"
    )
    img_bytes2 = fig2.to_image(format="png")
    imagens.append(img_bytes2)

    return imagens

# -----------------------------
# Função para enviar relatório por e-mail com gráficos
# -----------------------------
def enviar_relatorio_email(df, remetente, senha, destinatario):
    data_hoje = datetime.now().strftime("%d/%m/%Y")
    total_registros = len(df)
    total_lancamentos = (df["Tipo"] == "Lançamento").sum()
    total_baixas = (df["Tipo"] == "Baixa").sum()
    total_colaboradores = df["Colaborador"].nunique()

    # Gera imagens dos gráficos
    imagens = gerar_graficos(df)

    # Monta e-mail
    msg = MIMEMultipart()
    msg["Subject"] = f"📊 Relatório Diário - {data_hoje}"
    msg["From"] = remetente
    msg["To"] = destinatario

    corpo_html = f"""
    <html>
    <body style="font-family: Arial; color: #333;">
        <h2>📅 Relatório Diário - {data_hoje}</h2>
        <p>Segue abaixo o resumo das operações registradas:</p>

        <h3>📌 Indicadores Gerais</h3>
        <ul>
            <li><b>Total de registros:</b> {total_registros}</li>
            <li><b>Lançamentos:</b> {total_lancamentos}</li>
            <li><b>Baixas:</b> {total_baixas}</li>
            <li><b>Colaboradores ativos:</b> {total_colaboradores}</li>
        </ul>

        <h3>📈 Gráficos</h3>
        <h4>Baixa de CT-e por colaborador</h4>
        <img src="cid:grafico1" width="600"/><br><br>
        <h4>Tempo Médio por Tipo de Operação</h4>
        <img src="cid:grafico2" width="600"/><br><br>

        <p>Atenciosamente,
            <br><br>
            <b>IRAPURU TRANSPORTES LTDA</b><br>
            <b>Sistema de monitoramento Operacional</b><br>
            <b>Bot system</b><br>
        </p>
    </body>
    </html>
    """
    msg.attach(MIMEText(corpo_html, "html"))

    # Anexa imagens
    for i, img_bytes in enumerate(imagens, start=1):
        img = MIMEImage(img_bytes)
        img.add_header("Content-ID", f"<grafico{i}>")
        msg.attach(img)

    # Envio SMTP
    with smtplib.SMTP("smtp.gmail.com", 587) as server:
        server.starttls()
        server.login(remetente, senha)
        server.send_message(msg)

    print("✅ Relatório diário enviado com sucesso!")
