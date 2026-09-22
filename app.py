import os
import re
import time
import io
import streamlit as st
from google import genai
from google.genai import types

# Importações para geração do PDF via ReportLab
from reportlab.lib.pagesizes import letter
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.platypus import SimpleDocTemplate, Paragraph, Spacer, HRFlowable
from reportlab.lib import colors

# Configuração da Página do Streamlit
st.set_page_config(
    page_title="Risco AG & FBC - Decision Engine & Credit Rating",
    page_icon="📊",
    layout="wide",
    initial_sidebar_state="collapsed"
)

# Estilização CSS para interface escura e limpa
st.markdown("""
    <style>
    [data-testid="stSidebar"] {
        display: none !important;
    }
    [data-testid="collapsedControl"] {
        display: none !important;
    }
    .block-container {
        padding-top: 2rem !important;
        max-width: 95% !important;
    }
    .stApp {
        background-color: #0f172a;
        color: #f8fafc;
    }
    h1, h2, h3, h4, h5, h6, label, p, span, .stMarkdown {
        color: #f8fafc !important;
    }
    code {
        background-color: transparent !important;
        color: #f8fafc !important;
        border: none !important;
        padding: 0 !important;
        font-family: inherit !important;
        font-size: inherit !important;
        font-weight: inherit !important;
    }
    [data-testid="stFileUploaderDropzone"] {
        background-color: #1e293b !important;
        border: 2px dashed #475569 !important;
        border-radius: 8px !important;
    }
    [data-testid="stFileUploaderDropzone"] button {
        background-color: #334155 !important;
        color: #ffffff !important;
        border: 1px solid #64748b !important;
        border-radius: 6px !important;
    }
    [data-testid="stFileUploaderDropzone"] button:hover {
        background-color: #475569 !important;
        color: #ffffff !important;
    }
    [data-testid="stFileUploaderDropzone"] span, 
    [data-testid="stFileUploaderDropzone"] small,
    [data-testid="stFileUploaderFileData"] {
        color: #cbd5e1 !important;
    }
    .stButton>button {
        background-color: #10b981 !important;
        color: #0f172a !important;
        font-weight: bold !important;
        border-radius: 8px !important;
        border: none !important;
        padding: 0.6rem 1.2rem !important;
        width: 100% !important;
        font-size: 1.05rem !important;
    }
    .stButton>button:hover {
        background-color: #34d399 !important;
        color: #0f172a !important;
    }
    .stDownloadButton>button {
        background-color: #3b82f6 !important;
        color: #ffffff !important;
        font-weight: bold !important;
        border-radius: 8px !important;
        border: none !important;
        padding: 0.6rem 1.2rem !important;
        width: 100% !important;
        font-size: 1.05rem !important;
    }
    .stDownloadButton>button:hover {
        background-color: #60a5fa !important;
        color: #ffffff !important;
    }
    .stAlert {
        background-color: #1e293b !important;
        border: 1px solid #334155 !important;
    }
    div[data-baseweb="input"] {
        background-color: #1e293b !important;
        border-color: #334155 !important;
        color: #f8fafc !important;
    }
    </style>
""", unsafe_allow_html=True)

# -----------------------------------------------------------------------------
# AUTENTICAÇÃO POR LOGIN E SENHA
# -----------------------------------------------------------------------------
def check_password():
    def password_entered():
        users = st.secrets.get("passwords", {})
        username = st.session_state.get("username", "").strip()
        password = st.session_state.get("password", "").strip()

        if username in users and users[username] == password:
            st.session_state["password_correct"] = True
            del st.session_state["password"]
            del st.session_state["username"]
        else:
            st.session_state["password_correct"] = False

    if "password_correct" not in st.session_state:
        col_a, col_b, col_c = st.columns([3, 4, 3])
        with col_b:
            st.title("🔒 Acesso Restrito")
            st.caption("RISCO AG / FBC — Decision Engine")
            st.markdown("---")
            st.text_input("Usuário", key="username")
            st.text_input("Senha", type="password", key="password")
            st.button("Entrar no Sistema", on_click=password_entered)
        return False

    elif not st.session_state["password_correct"]:
        col_a, col_b, col_c = st.columns([3, 4, 3])
        with col_b:
            st.title("🔒 Acesso Restrito")
            st.caption("RISCO AG / FBC — Decision Engine")
            st.markdown("---")
            st.text_input("Usuário", key="username")
            st.text_input("Senha", type="password", key="password")
            st.button("Entrar no Sistema", on_click=password_entered)
            st.error("😕 Usuário ou senha incorretos.")
        return False
    else:
        return True

if not check_password():
    st.stop()

# -----------------------------------------------------------------------------
# GERADOR DE PDF DO PARECER
# -----------------------------------------------------------------------------
def gerar_pdf_relatorio(texto_relatorio, nomes_arquivos):
    buffer = io.BytesIO()
    doc = SimpleDocTemplate(
        buffer,
        pagesize=letter,
        rightMargin=40,
        leftMargin=40,
        topMargin=40,
        bottomMargin=40
    )
    
    styles = getSampleStyleSheet()
    
    style_title = ParagraphStyle(
        'DocTitle',
        parent=styles['Heading1'],
        fontName='Helvetica-Bold',
        fontSize=16,
        leading=20,
        textColor=colors.HexColor('#0f172a'),
        spaceAfter=4
    )
    
    style_subtitle = ParagraphStyle(
        'DocSubtitle',
        parent=styles['Normal'],
        fontName='Helvetica',
        fontSize=9,
        leading=12,
        textColor=colors.HexColor('#475569'),
        spaceAfter=12
    )
    
    style_heading = ParagraphStyle(
        'SectionHeader',
        parent=styles['Heading2'],
        fontName='Helvetica-Bold',
        fontSize=12,
        leading=15,
        textColor=colors.HexColor('#1e3a8a'),
        spaceBefore=10,
        spaceAfter=5
    )
    
    style_body = ParagraphStyle(
        'BodyTextCustom',
        parent=styles['Normal'],
        fontName='Helvetica',
        fontSize=9.5,
        leading=13.5,
        textColor=colors.HexColor('#1e293b'),
        spaceAfter=5
    )

    story = []
    
    story.append(Paragraph("RISCO AG / FBC — PARECER DE CRÉDITO & RATING JURÍDICO", style_title))
    story.append(Paragraph(f"Documentos Auditados ({len(nomes_arquivos)} arquivo(s)): {', '.join(nomes_arquivos)}", style_subtitle))
    story.append(HRFlowable(width="100%", thickness=1.5, color=colors.HexColor('#10b981'), spaceAfter=12))
    
    linhas = texto_relatorio.split('\n')
    for linha in linhas:
        linha_limpa = linha.strip()
        if not linha_limpa:
            story.append(Spacer(1, 3))
            continue
            
        linha_formatted = re.sub(r'\*\*(.*?)\*\*', r'<b>\1</b>', linha_limpa)
        
        if linha_limpa.startswith('# ') or linha_limpa.startswith('## ') or linha_limpa.startswith('### '):
            header_text = re.sub(r'^#+\s*', '', linha_formatted)
            story.append(Paragraph(header_text, style_heading))
        elif linha_limpa.startswith('- ') or linha_limpa.startswith('* '):
            bullet_text = re.sub(r'^[\-\*]\s*', '', linha_formatted)
            story.append(Paragraph(f"• {bullet_text}", style_body))
        else:
            story.append(Paragraph(linha_formatted, style_body))
            
    doc.build(story)
    buffer.seek(0)
    return buffer.getvalue()

# Obtém a chave da API nos Secrets
api_key = st.secrets.get("GEMINI_API_KEY", os.environ.get("GEMINI_API_KEY", "")).strip()

# Cabeçalho
col_tit, col_logout = st.columns([9, 1])
with col_tit:
    st.title("RISCO AG / FBC")
    st.caption("Motor de Decisão, Auditoria do Passivo Judicial e Rating de Crédito Agrícola")
with col_logout:
    st.markdown("<br>", unsafe_allow_html=True)
    if st.button("Sair"):
        st.session_state["password_correct"] = False
        st.rerun()

st.markdown("---")

# Layout Principal
col_left, col_right = st.columns([4, 8])

with col_left:
    st.subheader("Envio de Processos (Múltiplos PDFs)")
    uploaded_files = st.file_uploader(
        "Arraste ou selecione um ou mais PDFs dos autos (Cível, Trabalhista, Criminal, Ambiental, etc.):",
        type=["pdf"],
        accept_multiple_files=True
    )
    
    btn_processar = st.button("Gerar Rating e Diagnóstico Integrado", disabled=(not uploaded_files))

# SYSTEM INSTRUCTION COM REGRA DE ANÁLISE INDIVIDUALIZADA + CONSOLIDADA
SYSTEM_INSTRUCTION = """
Você é o Comitê de Risco de Crédito e Rating Jurídico do RISCO AG / FBC. Sua função é auditar os autos judiciais fornecidos — que podem abranger um ou múltiplos processos/recursos de naturezas distintas (Cível, Trabalhista, Criminal, Ambiental, etc.) contra o mesmo tomador — sob a ótica EXCLUSIVA de TOMADA DE DECISÃO DE CRÉDITO.

Você NÃO é o advogado das partes. NUNCA sugira estratégias de cobrança ou execução contra o réu. Sua missão é proteger a carteira de crédito da consulente contra o risco de default, estipulando a alçada, o rating, a matriz de garantias, o protocolo de campo e os filtros ESG.

DIRETRIZ DE ANÁLISE PARA MÚLTIPLOS PROCESSOS (AÇÕES HETEROGÊNEAS):
Caso sejam enviados 2 ou mais arquivos PDF (mesmo de naturezas distintas sem relação direta entre si), você DEVE:
1. Apresentar primeiro a ANÁLISE INDIVIDUALIZADA de cada processo enviada.
2. Apresentar em seguida o PARECER ESTRATÉGICO CONSOLIDADO, somando a exposição financeira total, mapeando o pico de risco reputacional/ESG e emitindo a decisão final do Comitê.

ESTRUTURA OBRIGATÓRIA DO RELATÓRIO DE SAÍDA:

1. DIAGNÓSTICO INDIVIDUALIZADO DOS PROCESSOS ENVIADOS
   Para cada PDF enviado, apresente um resumo cirúrgico contendo:
   - Identificação do Processo, Juízo, Classe e Natureza (Cível, Trabalhista, Criminal, Ambiental).
   - Polo do Tomador (Devedor Principal vs. Coobrigado/Avalista).
   - Valor do Passivo Judicial e Status das Liminares (Deferida com Ordem de Bloqueio/Arresto vs. Pendente).
   - Risco Específico Identificado (ex: risco de SISBAJUD no cível, risco de penhora de contas no trabalhista, risco reputacional no criminal, risco de embargo/perda de Selo MAPA no ambiental).

2. SÍNTESE DA EXPOSIÇÃO CONSOLIDADA E IMR GLOBAL
   - Passivo Judicial Total Consolidado (Soma de todos os processos).
   - IMR Global (Índice de Materialidade de Risco) x Exposição Estimada da Safra. Faixa: Baixa (<5%), Média (5%-15%), Alta (15%-30%) ou Crítica (>30%).
   - Detecção de Conexos Ausentes: Se algum processo citar outros autos/recursos relevantes não anexados, insira: "⚠️ PENDÊNCIA DOCUMENTAL: Recomenda-se o upload dos autos conexos [Nome do Processo] para auditoria complementar."

3. FILTRO RÍGIDO ESG, SELO MAPA E RISCO REPUTACIONAL / IMAGEM (CONSOLIDADO)
   - VETO AUTOMÁTICO (REPROVAÇÃO INCONDICIONAL): Se em qualquer dos processos constar Trabalho Escravo/Análogo, Trabalho Infantil ou Invasão de Terras Indígenas/Quilombolas/Unidades de Conservação ("Lista Suja" ou Ação Civil Pública).
   - CONDICIONANTES ESG: Para embargos ambientais (IBAMA/CAR), exigir delimitação da área financiada fora do polígono embargado, preservação do Selo MAPA e cláusula de vencimento antecipado por infração ambiental.

4. PARECER FINAL DO COMITÊ DE CRÉDITO E MATRIZ DE RECOMENDAÇÃO (INTEGRADO)
   - Rating Integrado Global: Calibrado pelo maior nível de risco do conjunto (Mínimo / Baixo / Moderado / Alto / Crítico).
   - Recomendação de Limite: (Aprovado / Aprovado com Condicionantes / Reprovado).
   - MATRIZ DE GARANTIAS CUMULATIVAS (Aplica-se em caso de aprovação):
     a) Risco Crítico / Alto (Se o Comitê aprovar contra a recomendação nativa): EXIGIR PELO MENOS 3 GARANTIAS SIMULTÂNEAS: [1] CPR Financeira/Física com Alienação Fiduciária de Imóvel Rural limpo ou Produto; [2] Cessão de Crédito formalizada com notificação e aceite de Trading de 1ª Linha (Bunge, Cargill, ADM, LDC, Amaggi); [3] Aval Cruzado Obrigatório de TODOS que produzem ou exploram a área.
     b) Risco Moderado / Médio: EXIGIR PELO MENOS 2 DAS GARANTIAS ACIMA.
     c) Risco Baixo / Seguro: EXIGIR PELO MENOS 1 DAS GARANTIAS PRINCIPAIS.
   - PROTOCOLO DE MONITORAMENTO DE LAVOURA (CAMPO):
     a) Risco Crítico / Alto: Monitoramento Terceirizado 24h na lavoura e embarque.
     b) Risco Moderado / Médio: Monitoramento Terceirizado 48h em fases críticas (plantio/colheita).
     c) Risco Baixo / Seguro: Monitoramento/Visita Semanal pelo Consultor Comercial.

5. RECOMENDAÇÃO DE ANÁLISE CONJUNTA MULTI-VETORIAL (OBRIGATÓRIA)
   - Inserir o alerta: "Independente do Rating Jurídico apontado, este parecer DEVE ser analisado conjuntamente com as análises apartadas de: [1] Capacidade Financeira e Fluxo de Caixa da Safra; [2] Endividamento Bancário e Cetes (SCR/BACEN); [3] Alavancagem e Custo Operacional por Hectare; [4] Dossiê Socioambiental e Rastreabilidade de Grãos."

REGRA DE FORMATAÇÃO MONETÁRIA:
- Escreva todos os valores financeiros estritamente no formato R$ 0,00 (ex: R$ 130.958,18).
- NUNCA utilize crases (` `) nem formatação em bloco de código para valores, datas ou números.
"""

with col_right:
    st.subheader("📊 Diagnóstico Integrado de Risco & Decisão de Crédito")
    
    if btn_processar and uploaded_files:
        if not api_key:
            st.error("Chave de API não configurada. Verifique as 'Secrets' no painel do Streamlit Cloud.")
        else:
            temp_paths = []
            arquivos_gemini = []
            nomes_arquivos = [f.name for f in uploaded_files]
            
            try:
                client = genai.Client(api_key=api_key)
                
                with st.spinner(f"Enviando e processando {len(uploaded_files)} PDF(s) para análise individualizada e consolidada via Gemini 3.6 Flash..."):
                    for file in uploaded_files:
                        temp_path = f"temp_{file.name}"
                        with open(temp_path, "wb") as f:
                            f.write(file.getbuffer())
                        temp_paths.append(temp_path)
                        
                        arq_uploaded = client.files.upload(file=temp_path)
                        arquivos_gemini.append(arq_uploaded)

                    contents_payload = list(arquivos_gemini)
                    contents_payload.append(
                        "Realize o diagnóstico completo deste tomador. Se houver 2 ou mais arquivos, apresente primeiro a análise individualizada de cada processo (Cível, Trabalhista, Criminal, Ambiental) e, em seguida, o parecer estratégico consolidado conforme as instruções do sistema."
                    )
                    
                    config = types.GenerateContentConfig(
                        system_instruction=SYSTEM_INSTRUCTION,
                        temperature=0.1,
                    )
                    
                    response = client.models.generate_content(
                        model="gemini-3.6-flash",
                        contents=contents_payload,
                        config=config,
                    )
                    
                    for arq in arquivos_gemini:
                        client.files.delete(name=arq.name)
                        
                    for tp in temp_paths:
                        if os.path.exists(tp):
                            os.remove(tp)

                    if response and response.text:
                        st.success(f"Análise Integrada de {len(uploaded_files)} arquivo(s) concluída com sucesso!")
                        
                        texto_formatado = response.text
                        texto_formatado = re.sub(r'R\s+(\d)', r'R$ \1', texto_formatado)
                        texto_formatado = re.sub(r'R\$\s*', r'R$ ', texto_formatado)
                        
                        st.markdown(texto_formatado)
                        
                        pdf_bytes = gerar_pdf_relatorio(texto_formatado, nomes_arquivos)
                        
                        st.markdown("---")
                        st.download_button(
                            label="📥 Baixar Parecer Completo Integrado em PDF",
                            data=pdf_bytes,
                            file_name=f"Parecer_Credito_Integrado_{len(uploaded_files)}_autos.pdf",
                            mime="application/pdf"
                        )
                    else:
                        st.error("Não foi possível obter resposta do modelo. Tente novamente.")

            except Exception as e:
                st.error(f"Erro no processamento: {str(e)}")
                for arq in arquivos_gemini:
                    try:
                        client.files.delete(name=arq.name)
                    except:
                        pass
                for tp in temp_paths:
                    if os.path.exists(tp):
                        os.remove(tp)
    else:
        st.info("Aguardando upload de um ou mais arquivos PDF para gerar o parecer de crédito e a matriz de mitigação.")
