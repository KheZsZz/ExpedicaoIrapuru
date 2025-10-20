from datetime import datetime
import smtplib
import plotly.express as px
from email.mime.multipart import MIMEMultipart
from email.mime.text import MIMEText
import plotly.io as pio
import streamlit as st

# -----------------------------
# 1️⃣ Função para gerar gráficos
# -----------------------------
def gerar_graficos_html(df):
    # Gráfico 1 - CT-e por colaborador
    fig1 = px.pie(
        df[df["Tipo"] == "Baixa"],
        names="Colaborador",
        values="QTD de CT-e",
        title="Distribuição de CT-e por Colaborador",
        hole=0.4,
        color="Colaborador",
    )
    fig1.update_traces(
        textinfo='percent+label+value',
        textfont_size=14,
        hovertemplate="<b>%{label}</b><br>CT-es: %{value}<br>Percentual: %{percent}",
    )

    # Gráfico 2 - Tempo médio por tipo
    tempo_tipo = df.groupby("Tipo")["Total (min)"].mean().reset_index()
    fig2 = px.bar(
        tempo_tipo,
        x="Tipo",
        y="Total (min)",
        title="Tempo Médio por Tipo de Operação (min)",
        text_auto=".1f",
        color="Tipo",
    )

    # Converte gráficos para HTML interativo
    fig1_html = pio.to_html(fig1, full_html=False, include_plotlyjs='cdn')
    fig2_html = pio.to_html(fig2, full_html=False, include_plotlyjs=False)  # usa mesmo PlotlyJS do fig1

    return fig1_html, fig2_html


# -----------------------------
# 2️⃣ Função para enviar relatório por e-mail com gráficos HTML
# -----------------------------
def enviar_relatorio_email_html(df, remetente, senha, destinatario):
    data_hoje = datetime.now().strftime("%d/%m/%Y")

    # Indicadores
    total_registros = len(df)
    total_lancamentos = (df["Tipo"] == "Lançamento").sum()
    total_baixas = (df["Tipo"] == "Baixa").sum()
    total_colaboradores = df["Colaborador"].nunique()

    # Gera gráficos HTML
    fig1_html, fig2_html = gerar_graficos_html(df)

    # Monta e-mail HTML
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

        <h3>📈 Gráficos Interativos</h3>
        <h4>Baixa de CT-e por colaborador</h4>
        {fig1_html}<br><br>

        <h4>Tempo Médio</h4>
        {fig2_html}<br><br>

        <p>Atenciosamente,
            <br><br>
            <b>IRAPURU TRANSPORTES LTDA</b><br>
            <b>Sistema de monitoramento Operacional</b><br>
            <b>Bot system</b><br>
        </p>
    </body>
    </html>
    """

    # Monta e-mail
    msg = MIMEMultipart()
    msg["Subject"] = f"📊 Relatório Diário - {data_hoje}"
    msg["From"] = remetente
    msg["To"] = destinatario
    msg.attach(MIMEText(corpo_html, "html"))

    # Envio SMTP
    with smtplib.SMTP("smtp.gmail.com", 587) as server:
        server.starttls()
        server.login(remetente, senha)
        server.send_message(msg)

    print("✅ Relatório diário enviado com sucesso!")
