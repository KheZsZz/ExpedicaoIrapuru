from datetime import datetime
import smtplib
import plotly.express as px
from email.mime.multipart import MIMEMultipart
from email.mime.text import MIMEText
from email.mime.image import MIMEImage
import io
from PIL import Image

# -----------------------------
# 1️⃣ Função para gerar gráficos e salvar imagens
# -----------------------------
def gerar_graficos(df):
    # Gráfico 1 - CT-e por colaborador
    fig1 = px.pie(
        df[df["Tipo"] == "Baixa"],
        names="Colaborador",
        values="QTD de CT-e",
        title="Distribuição de CT-e por Colaborador",
        hole=0.4,
        color= "Colaborador",
    )
    fig1.update_traces(
        textinfo='percent+label+value',
        textfont_size=14,
        hovertemplate="<b>%{label}</b><br>CT-es: %{value}<br>Percentual: %{percent}",
    )
    img_bytes = fig1.to_image(format="png")  # usa engine interno, sem Chrome
    img_buffer = io.BytesIO(img_bytes)
    image = Image.open(img_buffer)

    # Salva localmente (opcional)
    image.save("grafico_cte_colaborador.png")

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
    img_bytes = fig1.to_image(format="png")  # usa engine interno, sem Chrome
    img_buffer = io.BytesIO(img_bytes)
    image = Image.open(img_buffer)

    # Salva localmente (opcional)
    image.save("grafico_tempo_tipo.png")
    return fig1, fig2


# -----------------------------
# 2️⃣ Função para montar e enviar e-mail
# -----------------------------
def enviar_relatorio_email(df, remetente, senha, destinatario):
    data_hoje = datetime.now().strftime("%d/%m/%Y")

    # Resumo dos indicadores
    total_registros = len(df)
    total_lancamentos = (df["Tipo"] == "Lançamento").sum()
    total_baixas = (df["Tipo"] == "Baixa").sum()
    total_colaboradores = df["Colaborador"].nunique()

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
        <h4>Tempo Médio</h4>
        <img src="cid:grafico2" width="600"/><br><br>

        <p>Atenciosamente,
            <br>
            <br>
            <br>
            <b>IRAPURU TRANSPORTES LTDA</b><br>
            <b>Sistema de monitoramento Operacional</b><br>
            <b>Bot system</b><br>
        </p>
    </body>
    </html>
    """

    msg.attach(MIMEText(corpo_html, "html"))

    # Anexa imagens
    for i, img_path in enumerate(["grafico_cte_colaborador.png", "grafico_tempo_tipo.png"], start=1):
        with open(img_path, "rb") as f:
            img = MIMEImage(f.read())
            img.add_header("Content-ID", f"<grafico{i}>")
            msg.attach(img)

    # Envio SMTP
    with smtplib.SMTP("smtp.gmail.com", 587) as server:
        server.starttls()
        server.login(remetente, senha)
        server.send_message(msg)

    print("✅ Relatório diário enviado com sucesso!")