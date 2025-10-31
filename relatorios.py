# relatorios.py
import io
import os
import smtplib
from datetime import datetime
from email.mime.multipart import MIMEMultipart
from email.mime.text import MIMEText
from email.mime.image import MIMEImage
import matplotlib.pyplot as plt
import matplotlib.cm as cm
import pandas as pd
from database import conectData, ocorrenciasRecebimento

df_CTe = conectData()
df_ocorrencias = ocorrenciasRecebimento()

# -----------------------------
# 1️⃣ Função para gerar gráficos
# -----------------------------
def gerar_graficos(df):
    imagens = []

    if df is None or df.empty:
        return imagens

    # ======== GRÁFICO 1 - CT-e por colaborador (pizza) ========
    df_baixa = df[df["Tipo"].str.lower() == "baixa"].copy()

    if not df_baixa.empty and {"QTD de CT-e", "Colaborador"}.issubset(df_baixa.columns):
        df_baixa["QTD de CT-e"] = pd.to_numeric(df_baixa["QTD de CT-e"], errors="coerce").fillna(0)
        cte_por_colab = df_baixa.groupby("Colaborador")["QTD de CT-e"].sum()

        if not cte_por_colab.empty:
            fig1, ax1 = plt.subplots(figsize=(6, 6))
            ax1.pie(
                cte_por_colab,
                labels=cte_por_colab.index,
                autopct=lambda p: f"{p:.1f}%\n{p * cte_por_colab.sum() / 100:.0f} CT-e",
                startangle=90,
                colors=cm.get_cmap("tab20", len(cte_por_colab)).colors,
                explode=[0.1 if v == cte_por_colab.max() else 0 for v in cte_por_colab],
                textprops={"fontsize": 9},
            )
            ax1.set_title("Baixa de CT-e por Colaborador", fontsize=12)
        else:
            fig1, ax1 = plt.subplots(figsize=(6, 6))
            ax1.text(0.5, 0.5, "Sem dados de CT-e por colaborador", ha="center", va="center", fontsize=11)
            ax1.axis("off")
    else:
        fig1, ax1 = plt.subplots(figsize=(6, 6))
        ax1.text(0.5, 0.5, "Sem dados de baixas", ha="center", va="center", fontsize=11)
        ax1.axis("off")

    buf1 = io.BytesIO()
    fig1.savefig(buf1, format="png", bbox_inches="tight")
    buf1.seek(0)
    imagens.append(buf1)
    plt.close(fig1)

    # ======== GRÁFICO 2 - Tempo médio por tipo (barra) ========
    if {"Tipo", "Total (min)"}.issubset(df.columns):
        tempo_tipo = df.groupby("Tipo")["Total (min)"].mean()

        if not tempo_tipo.empty:
            tempo_tipo = tempo_tipo / 60  # converter minutos em horas
            fig2, ax2 = plt.subplots(figsize=(8, 5))
            ax2.bar(
                tempo_tipo.index,
                tempo_tipo.values,
                color=cm.get_cmap("tab20", len(tempo_tipo)).colors,
            )
            ax2.set_title("Tempo Médio por Tipo de Operação (horas)", fontsize=12)
            ax2.set_ylabel("Horas")

            for i, v in enumerate(tempo_tipo.values):
                horas = int(v // 1)
                minutos = int((v % 1) * 60)
                ax2.text(i, v, f"{horas}h {minutos}m", ha="center", va="bottom", fontsize=9)
        else:
            fig2, ax2 = plt.subplots(figsize=(8, 5))
            ax2.text(0.5, 0.5, "Sem dados de tempo médio por tipo", ha="center", va="center", fontsize=11)
            ax2.axis("off")
    else:
        fig2, ax2 = plt.subplots(figsize=(8, 5))
        ax2.text(0.5, 0.5, "Colunas 'Tipo' ou 'Total (min)' ausentes", ha="center", va="center", fontsize=11)
        ax2.axis("off")

    buf2 = io.BytesIO()
    fig2.savefig(buf2, format="png", bbox_inches="tight")
    buf2.seek(0)
    imagens.append(buf2)
    plt.close(fig2)

    return imagens


# -----------------------------
# 2️⃣ Função para enviar e-mail
# -----------------------------
def enviar_relatorio_email(df, remetente, senha, destinatario, ocorrencias, turno, ctes):
    data_hoje = datetime.now().strftime("%d/%m/%Y")
    

    # ===== Verificação inicial =====
    if df is None or df.empty:
        corpo_html = f"""
        <html>
        <body style="font-family: Arial; color: #333;">
            <h2>📅 Relatório Diário</h2>
            <p>⚠️ Nenhum dado disponível para gerar o relatório de hoje.</p>
        </body>
        </html>
        """
        imagens = []
    else:
        # ===== Resumos =====
        total_registros = len(df)
        total_lancamentos = (df["Tipo"].str.lower() == "lançamento").sum()
        total_baixas = (df["Tipo"].str.lower() == "baixa").sum()
        total_abastecimentos = (df["Tipo"].str.lower() == "abastecimento").sum()
        
        total_colaboradores = df["Colaborador"].nunique()
        colaboradores = ", ".join(sorted(df["Colaborador"].dropna().unique()))
        
        # Filtrar turno e data
        if "Todos os turnos" in turno: 
            df_filtrado_cte = ctes 
        else: 
            df_filtrado_cte = ctes[ctes["Turno"] == turno]
        
        df_filtrado_ocorrencias = df_ocorrencias[
            (df_ocorrencias["Data da ocorrência"] == datetime.now().strftime("%d/%m/%Y"))
        ]

        # Agrupar por responsável e somar a quantidade de CTe
        cte = df_filtrado_cte.groupby("Responsável", as_index=False).agg({"Quantidade de CTe": "sum"})

        if not cte.empty:
            cte_html = cte.to_html(index=False, border=0, justify="center", classes="tabela-relatorio")
        else:
            cte_html = f"<p><i>⚠️ Nenhum CTe registrado para o {turno} turno na data selecionada.</i></p>"
        
        if not df_filtrado_ocorrencias.empty:
            # Identifica o nome da última coluna (link)
            ultima_coluna = df_filtrado_ocorrencias.columns[-1]

            # Cria cópia para não afetar o original
            df_links = df_filtrado_ocorrencias.copy()

            # Converte links em HTML clicável com texto "Abrir Anexo 📎"
            df_links[ultima_coluna] = df_links[ultima_coluna].apply(
                lambda x: f'<a href="{x}" target="_blank">Abrir Anexo 📎</a>'
                if isinstance(x, str) and x.startswith("http")
                else x
            )

            # Seleciona colunas específicas na ordem desejada
            colunas_desejadas = [
                "Data da ocorrência",
                "Placa do veículo",
                "Setor responsável",
                "Descritivo do ocorrido",
                ultima_coluna,  # Evidências (última coluna com link)
            ]
            df_links = df_links[colunas_desejadas]

            # Gera HTML com links clicáveis
            ocorrencias_html = df_links.to_html(
                index=False,
                border=0,
                justify="center",
                classes="tabela-relatorio",
                escape=False  # Permite HTML nos links
            )
        else:
            ocorrencias_html = "<p><i>⚠️ Nenhuma ocorrência registrada para a data selecionada.</i></p>"

        
          
        def formatar_tempo(total_minutos):
            horas = int(total_minutos // 60)
            minutos = int(total_minutos % 60)
            return f"{horas:02d}H:{minutos:02d}M"
        
        tabela_resumo = (
            df[df["Destino"].str.lower() != "itapecerica da serra"]
            .groupby(["Destino", "Placa"], as_index=False)
            .agg({"Total (min)": "sum"})  # ou "mean" se quiser média
        )
        tabela_resumo["Total (min)"] = tabela_resumo["Total (min)"].apply(formatar_tempo)
        tabela_html = tabela_resumo.to_html(index=False, border=0, justify="center", classes="tabela-relatorio")

        imagens = gerar_graficos(df)
        
        corpo_html = f"""
        <html>
        <head>
            <style>
                body {{
                    font-family: Arial, sans-serif;
                    color: #333;
                }}
                ul {{
                    line-height: 1.6;
                }}
                .tabela-relatorio {{
                    border-collapse: collapse;
                    width: 100%;
                    margin-top: 10px;
                }}
                .tabela-relatorio th {{
                    background-color: #4CAF50;
                    color: white;
                    padding: 8px;
                    text-align: left;
                }}
                .tabela-relatorio td {{
                    padding: 6px;
                    border-bottom: 1px solid #ddd;
                }}
                .tabela-relatorio tr:nth-child(even) {{
                    background-color: #f2f2f2;
                }}
            </style>
        </head>
        <body>
            <h2>📅 Relatório Diário</h2>
            <p>Resumo das operações:</p>
            <ul>
                <li><b>Total de registros:</b> {total_registros}</li>
                <li><b>Lançamentos:</b> {total_lancamentos}</li>
                <li><b>Baixas:</b> {total_baixas}</li>
                <li><b>Abastecimentos:</b> {total_abastecimentos}</li>
                <li><b>Colaboradores ativos ({total_colaboradores}):</b> {colaboradores}</li>
            </ul>
            
            <h3> Quandidade de CT-e digitados </h3>
            {cte_html}

            <h3>🚚 Viagens fechadas</h3>
            {tabela_html}

            <h3>📈 Gráficos</h3>
        """

        if imagens:
            for i, _ in enumerate(imagens):
                corpo_html += f'<img src="cid:grafico{i+1}" width="600"/><br><br>'
        else:
            corpo_html += "<p><i>⚠️ Nenhum gráfico foi gerado por falta de dados.</i></p>"

                  # Dentro do corpo HTML do e-mail, inclua:
        if ocorrencias:
            ocorrencias = ocorrencias.replace("\n", "<br>")
            corpo_html += f"""
            <h3>⚠️ Ocorrências</h3>
            {ocorrencias_html}
            
            <h3>📌 Observações</h3>
            <p>{ocorrencias}</p>
            """
            
        corpo_html += """
                <br>
                <p>Atenciosamente,</p>
                <br>
                <img src="cid:assinatura" alt="Assinatura" width="620"/>
            </body>
            </html>"""


    # ===== Montagem da mensagem =====
    msg = MIMEMultipart()
    msg["Subject"] = f"📊 Fechamento"
    msg["From"] = remetente
    msg["To"] = destinatario
    msg.attach(MIMEText(corpo_html, "html"))

    # ===== Anexar imagens dos gráficos =====
    for i, img_buf in enumerate(imagens):
        img_buf.seek(0)
        img = MIMEImage(img_buf.read())
        img.add_header("Content-ID", f"<grafico{i+1}>")
        msg.attach(img)

    # ===== Anexar assinatura =====
    try:
        caminho_assinatura = os.path.join(os.getcwd(), "assinatura.png")
        with open(caminho_assinatura, "rb") as f:
            assinatura_img = MIMEImage(f.read())
            assinatura_img.add_header("Content-ID", "<assinatura>")
            msg.attach(assinatura_img)
    except Exception as e:
        print(f"⚠️ Erro ao anexar imagem de assinatura: {e}")
    
    # ===== Envio =====
    try:
        with smtplib.SMTP("smtp.gmail.com", 587) as smtp:
            smtp.starttls()
            smtp.login(remetente, senha)
            smtp.send_message(msg)
        print("✅ Relatório enviado com sucesso!")
    except Exception as e:
        print(f"❌ Erro ao enviar e-mail: {e}")
