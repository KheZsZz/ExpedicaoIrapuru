# relatorios.py
import io
import smtplib
from datetime import datetime
from email.mime.multipart import MIMEMultipart
from email.mime.text import MIMEText
from email.mime.image import MIMEImage
import matplotlib.pyplot as plt
import matplotlib.cm as cm
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
        autopct=lambda p: f'{p:.1f}% \n {p * cte_por_colab.sum() / 100:.0f} CT-e',
        startangle=90,
        colors = cm.get_cmap("tab20", len(cte_por_colab)).colors,
        explode = [0.1 if v == cte_por_colab.max() else 0 for v in cte_por_colab]
    )
    
    ax1.set_title("Baixa de CT-e por Colaborador")
    buf1 = io.BytesIO()
    fig1.savefig(buf1, format="png", bbox_inches="tight")
    buf1.seek(0)
    imagens.append(buf1)
    plt.close(fig1)

    # Gráfico 2 - Tempo médio por tipo (barra)
    tempo_tipo = df.groupby("Tipo")["Total (min)"].mean()
    tempo_tipo = tempo_tipo/60
    fig2, ax2 = plt.subplots(figsize=(8,5))
    ax2.bar(
        tempo_tipo.index,
        tempo_tipo.values,
        color=cm.get_cmap("tab20", len(tempo_tipo)).colors,
    )
    ax2.set_title("Tempo Médio por Tipo de Operação (min)")
    ax2.set_ylabel("Horas")
    for i, v in enumerate(tempo_tipo.values):
        horas = int(v // 60)
        minutos = int(v % 60)
        ax2.text(i, v + 0.5, f"{horas}h {minutos}m", ha="center", va="bottom" if v < 0 else "center")
    buf2 = io.BytesIO()
    fig2.savefig(buf2, format="png", bbox_inches="tight")
    buf2.seek(0)
    imagens.append(buf2)
    plt.close(fig2)

    return imagens

# -----------------------------
# 2️⃣ Função para enviar e-mail
# -----------------------------
def enviar_relatorio_email(df, remetente, senha, destinatario, subjects):
    imagens = gerar_graficos(df)
    data_hoje = datetime.now().strftime("%d/%m/%Y")

    total_registros = len(df)
    total_lancamentos = (df["Tipo"] == "Lançamento").sum()
    total_baixas = (df["Tipo"] == "Baixa").sum()
    total_colaboradores = df["Colaborador"].nunique()
    total_abastecimentos = (df["Tipo"] == "Abastecimento").sum()

    msg = MIMEMultipart()
    msg["Subject"] = f"📊 Relatório Diário - {data_hoje}"
    msg["From"] = remetente
    msg["To"] = destinatario
    msg["Subject"] = subjects
    
    corpo_html = f"""
    <html>
    <body style="font-family: Arial; color: #333;">
        <h2>📅 Relatório Diário - {data_hoje}</h2>
        <p>Resumo das operações (Expedição/Recebimento):</p>
        <ul>
            <li><b>Total de registros:</b> {total_registros}</li>
            <li><b>Tempo médio (min):</b> {df['Total (min)'].mean():.2f}</li>
            <li><b>Lançamentos:</b> {total_lancamentos}</li>
            <li><b>Baixas:</b> {total_baixas}</li>
            <li><b>Abastecimentos:</b> {total_abastecimentos}</li>
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
