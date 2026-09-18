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
    page_title="Risco AG | FBC - Decision Engine & Credit Rating",
    page_icon="📊",
    layout="wide",
    initial_sidebar_state="collapsed"
)

# Estilização CSS para interface limpa, profissional e identidade das marcas
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
    
    /* Estilização da Logo da Marca */
    .brand-header {
        font-size: 2.2rem;
        font-weight: 800;
        letter-spacing: -0.5px;
        margin-bottom: 0.2rem;
    }
    .brand-risco { color: #ffffff !important; }
    .brand-ag { color: #10b981 !important; }
    .brand-pipe { color: #ffffff !important; margin: 0 8px; }
    .brand-fbc { color: #e2e8f0 !important; }

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
    </style>
""", unsafe_allow_html=True)

# Função para gerar o arquivo PDF estilizado em memória
def gerar_pdf_relatorio(texto_relatorio, nome_arquivo_original):
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
    
    style_subtitle = ParagraphStyle(
        'DocSubtitle',
        parent=styles['Normal'],
        fontName='Helvetica',
        fontSize=10,
        leading=12,
        textColor=colors.HexColor('#475569'),
        spaceAfter=15
    )
    
    style_heading = ParagraphStyle(
        'SectionHeader',
        parent=styles['Heading2'],
        fontName='Helvetica-Bold',
        fontSize=12,
        leading=15,
        textColor=colors.HexColor('#1e3a8a'),
        spaceBefore=12,
        spaceAfter=6
    )
    
    style_body = ParagraphStyle(
        'BodyTextCustom',
        parent=styles['Normal'],
        fontName='Helvetica',
        fontSize=9.5,
        leading=13.5,
        textColor=colors.HexColor('#1e293b'),
        spaceAfter=6
    )

    story = []
    
    # Cabeçalho estilizado do PDF com FBC em cinza claro
    header_html = '<font color="#0f172a"><b>Risco</b></font> <font color="#10b981"><b>AG</b></font> <font color="#64748b">|</font> <font color="#475569"><b>FBC</b></font> <font size="12" color="#334155"> — Parecer de Crédito & Rating</font>'
    style_pdf_header = ParagraphStyle('PDFHeader', parent=styles['Heading1'], fontName='Helvetica-Bold', fontSize=18, leading=22, spaceAfter=4)
    
    story.append(Paragraph(header_html, style_pdf_header))
    story.append(Paragraph(f"Documento Auditado: {nome_arquivo_original} | Avaliação de Risco de Crédito", style_subtitle))
    story.append(HRFlowable(width="100%", thickness=1.5, color=colors.HexColor('#10b981'), spaceAfter=12))
    
    # Processa linhas de Markdown para converter em tags do ReportLab
    linhas = texto_relatorio.split('\n')
    for linha in linhas:
        linha_limpa = linha.strip()
        if not linha_limpa:
            story.append(Spacer(1, 4))
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

# Obtém a chave configurada nos Secrets
api_key = st.secrets.get("GEMINI_API_KEY", os.environ.get("GEMINI_API_KEY", "")).strip()

# Cabeçalho com Logo Ajustada
st.markdown('<div class="brand-header"><span class="brand-risco">Risco</span><span class="brand-ag">AG</span><span class="brand-pipe">|</span><span class="brand-fbc">FBC</span></div>', unsafe_allow_html=True)
st.caption("Motor de Decisão, Auditoria do Passivo Judicial e Rating de Crédito Agrícola")

st.markdown("---")

# Layout Principal
col_left, col_right = st.columns([4, 8])

with col_left:
    st.subheader("Envio do Processo")
    uploaded_file = st.file_uploader("Arraste ou selecione o PDF integral dos autos:", type=["pdf"])
    
    btn_processar = st.button("Gerar Rating e Diagnóstico", disabled=(uploaded_file is None))

SYSTEM_INSTRUCTION = """
Você é um Comitê de Risco de Crédito e Inteligência de Concessão especializado em Agronegócio. Sua função é auditar o passivo judicial exposto no processo analisado sob a ótica EXCLUSIVA de TOMADA DE DECISÃO DE CRÉDITO para uma futura operação de financiamento, fomento ou renegociação de dívida do tomador avaliado.

Você NÃO é o advogado das partes no processo. Portanto, NUNCA dê sugestões de estratégia de cobrança, execução, penhora judicial ou medidas processuais contra o réu.

Sua análise deve responder prioritariamente: "Qual o impacto deste processo no risco de crédito do tomador e sob quais estruturas, alçadas e garantias ele pode ser financiado ou renegociado?"

AO ANALISAR OS AUTOS, OBEDEÇA RIGOROSAMENTE À SEGUINTE ESTRUTURA DE DIAGNÓSTICO:

1. DADOS DE IDENTIFICAÇÃO E MATERIALIDADE
   - Identificação das Partes e Juízo.
   - Classe Processual e Origem do Débito.
   - Valor do Passivo Judicial Atualizado e Materialidade da Exposição.

2. AVALIAÇÃO DE EXPOSIÇÃO E SENSIBILIDADE OPERACIONAL
   - Risco de Constrição Imediata: Avaliar o risco real de o tomador sofrer bloqueio de contas (SISBAJUD), retenção de grãos ou arresto durante a vigência do novo crédito.
   - Comportamento de Defesa: Avaliar se o devedor demonstrou inércia/revelia ou se há teses defensivas relevantes.

3. PARECER DO COMITÊ DE CRÉDITO E RECOMENDAÇÃO DE CONCESSÃO
   - Diagnóstico Final de Rating de Crédito (Ex: Risco Baixo, Moderado, Alto ou Crítico).
   - Recomendação Final de Financiamento: (Aprovado / Aprovado com Condicionantes / Desfavorável).
   - ALÇADA DE APROVAÇÃO EXIGIDA (Determinar a alçada necessária com base no valor da exposição/passivo analisado):
     * Até R$ 500.000,00: Coordenador de Crédito
     * Acima de R$ 500.000,00 e até R$ 1.000.000,00: Gerente de Crédito
     * Acima de R$ 1.000.000,00: CFO (Chief Financial Officer)
   - ESTRUTURAÇÃO DE GARANTIAS E CONDICIONANTES DA OPERAÇÃO:
     Aplique estritamente as diretrizes de garantia da política de crédito:
     a) Operações de Barter (Permuta/Troca de Insumos por Grãos): Exigir obrigatoriamente CPR Física com Penhor Agrícola registrado sobre a safra futura.
     b) Operações de Renegociação de Dívida / Financiamento sem Barter: Exigir obrigatoriamente CPR Física ou CPR Financeira acompanhada de Alienação Fiduciária de Imóvel Rural isento de ônus e/ou Alienação Fiduciária de Produto Agrícola.
     c) Liquidação da Operação / Trava de Recebimento: Requerer a cessão de crédito estruturada com notificação e aceite de Trading de primeira linha (ex: Bunge, Cargill, ADM, LDC, Amaggi).

4. NOTA DE ISENÇÃO DE RESPONSABILIDADE E CONFORMIDADE ÉTICA (OBRIGATÓRIO NO FINAL DO PARECER):
   Insira obrigatoriamente a seguinte ressalva ao final de todo diagnóstico gerado:
   "DISCLAIMER INSTITUCIONAL: Este parecer constitui uma análise técnica instrumental de apoio à tomada de decisão de risco e concessão de crédito agrícola. As conclusões e recomendações de garantia fornecidas não substituem a análise e validação jurídica formal da operação. Recomendamos expressamente que o Departamento Jurídico interno ou a assessoria jurídica externa do consulente seja consultada para validação dos instrumentos contratuais, minutas e viabilidade de registro das garantias propostas."

REGRA DE FORMATAÇÃO:
- Escreva todos os valores estritamente no formato R$ 0,00 (ex: R$ 130.958,18).
- NUNCA utilize crases (` `) para destacar valores, números, IDs ou datas.
"""

with col_right:
    st.subheader("📊 Diagnóstico de Risco & Decisão de Crédito")
    
    if btn_processar and uploaded_file is not None:
        if not api_key:
            st.error("Chave de API não configurada. Verifique as 'Secrets' no painel do Streamlit Cloud.")
        else:
            temp_path = f"temp_{uploaded_file.name}"
            with open(temp_path, "wb") as f:
                f.write(uploaded_file.getbuffer())

            with st.spinner("Analisando autos sob a ótica de Risco, Alçadas e Concessão de Crédito..."):
                try:
                    client = genai.Client(api_key=api_key)
                    
                    arquivo_processo = client.files.upload(file=temp_path)
                    
                    config = types.GenerateContentConfig(
                        system_instruction=SYSTEM_INSTRUCTION,
                        temperature=0.1,
                    )
                    
                    response = client.models.generate_content(
                        model="gemini-3.6-flash",
                        contents=[
                            arquivo_processo,
                            "Realize o diagnóstico completo de Risco e Decisão de Concessão de Crédito deste tomador com base nos autos, especificando a Alçada de Aprovação requerida, garantias necessárias e o disclaimer institucional.",
                        ],
                        config=config,
                    )
                    
                    client.files.delete(name=arquivo_processo.name)
                    os.remove(temp_path)
                    
                    if response and response.text:
                        st.success("Análise de Concessão de Crédito concluída com sucesso!")
                        
                        # Formatação para exibição limpa dos valores
                        texto_formatado = response.text
                        texto_formatado = re.sub(r'R\s+(\d)', r'R$ \1', texto_formatado)
                        texto_formatado = re.sub(r'R\$\s*', r'R$ ', texto_formatado)
                        
                        # Exibe a análise na tela
                        st.markdown(texto_formatado)
                        
                        # Gera o PDF em memória para download
                        pdf_bytes = gerar_pdf_relatorio(texto_formatado, uploaded_file.name)
                        
                        st.markdown("---")
                        st.download_button(
                            label="📥 Baixar Parecer Completo em PDF",
                            data=pdf_bytes,
                            file_name=f"Parecer_Credito_{uploaded_file.name.replace('.pdf', '')}.pdf",
                            mime="application/pdf"
                        )
                    else:
                        st.error("Não foi possível obter resposta do modelo. Tente novamente.")
                        
                except Exception as e:
                    st.error(f"Erro no processamento: {str(e)}")
                    if os.path.exists(temp_path):
                        os.remove(temp_path)
    else:
        st.info("Aguardando upload de arquivo PDF para gerar o parecer de crédito e a matriz de mitigação.")
