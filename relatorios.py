# relatorios.py
import io
import smtplib
from datetime import datetime
from email.mime.multipart import MIMEMultipart
from email.mime.text import MIMEText
from email.mime.image import MIMEImage
import matplotlib.pyplot as plt
import pandas as pd

# -----------------------------
# 1️⃣ Função para gerar gráficos com Matplotlib
# -----------------------------
def gerar_graficos(df):
    imagens = []

    # Gráfico 1 - CT-e por colaborador (pizza)
    df_baixa = df[df["Tipo"].str.lower() == "baixa"]
    df_baixa["QTD de CT-e"] = pd.to_numeric(df_baixa["QTD de CT-e"], errors="coerce").fillna(0)
    cte_por_colab = df_baixa.groupby("Colaborador")["QTD de CT-e"].sum()

    fig1, ax1 = plt.subplots(figsize=(6,6))
    ax1.pie(
        cte_por_colab,
        labels=cte_por_colab.index,
        autopct="%1.1f%%",
        startangle=90
    )
    ax1.set_title("Distribuição de CT-e por Colaborador")
    buf1 = io.BytesIO()
    fig1.savefig(buf1, format="png", bbox_inches="tight")
    buf1.seek(0)
    imagens.append(buf1)
    plt.close(fig1)

    # Gráfico 2 - Tempo médio por tipo (barra)
    tempo_tipo = df.groupby("Tipo")["Total (min)"].mean()
    fig2, ax2 = plt.subplots(figsize=(8,5))
    ax2.bar(tempo_tipo.index, tempo_tipo.values, color="skyblue")
    ax2.set_title("Tempo Médio por Tipo de Operação (min)")
    ax2.set_ylabel("Minutos")
    for i, v in enumerate(tempo_tipo.values):
        ax2.text(i, v + 0.5, f"{v:.1f}", ha="center")
    buf2 = io.BytesIO()
    fig2.savefig(buf2, format="png", bbox_inches="tight")
    buf2.seek(0)
    imagens.append(buf2)
    plt.close(fig2)

    return imagens

# -----------------------------
# 2️⃣ Função para enviar e-mail
# -----------------------------
def enviar_relatorio_email(df, remetente, senha, destinatario):
    imagens = gerar_graficos(df)
    data_hoje = datetime.now().strftime("%d/%m/%Y")

    total_registros = len(df)
    total_lancamentos = (df["Tipo"] == "Lançamento").sum()
    total_baixas = (df["Tipo"] == "Baixa").sum()
    total_colaboradores = df["Colaborador"].nunique()

    msg = MIMEMultipart()
    msg["Subject"] = f"📊 Relatório Diário - {data_hoje}"
    msg["From"] = remetente
    msg["To"] = destinatario

    corpo_html = f"""
    <html>
    <body style="font-family: Arial; color: #333;">
        <h2>📅 Relatório Diário - {data_hoje}</h2>
        <p>Resumo das operações:</p>
        <ul>
            <li><b>Total de registros:</b> {total_registros}</li>
            <li><b>Lançamentos:</b> {total_lancamentos}</li>
            <li><b>Baixas:</b> {total_baixas}</li>
            <li><b>Colaboradores ativos:</b> {total_colaboradores}</li>
        </ul>

        <h3>📈 Gráficos</h3>
        <h4>Baixa de CT-e por colaborador</h4>
        <img src="cid:grafico1" width="600"/><br><br>
        <h4>Tempo médio por tipo</h4>
        <img src="cid:grafico2" width="600"/><br><br>
    </body>
    </html>
    """
    msg.attach(MIMEText(corpo_html, "html"))

    # Anexa imagens
    for i, buf in enumerate(imagens, start=1):
        img = MIMEImage(buf.read())
        img.add_header("Content-ID", f"<grafico{i}>")
        msg.attach(img)
        buf.close()

    # Envia e-mail via SMTP
    with smtplib.SMTP("smtp.gmail.com", 587) as server:
        server.starttls()
        server.login(remetente, senha)
        server.send_message(msg)

    print("✅ Relatório enviado com sucesso!")
