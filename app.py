import os
import time
import streamlit as st
from google import genai
from google.genai import types
from google.genai.errors import APIError

# Configuração da Página do Streamlit
st.set_page_config(
    page_title="Risco AG & FBC - Auditoria Jurídica & Rating",
    page_icon="📊",
    layout="wide"
)

# Estilização CSS completa
st.markdown("""
    <style>
    /* Ajuste de espaçamento superior para não cortar o título */
    .block-container {
        padding-top: 2rem !important;
    }
    
    /* Fundo geral da aplicação */
    .stApp {
        background-color: #0f172a;
        color: #f8fafc;
    }
    
    /* Textos principais e cabeçalhos */
    h1, h2, h3, h4, h5, h6, label, p, span, .stMarkdown {
        color: #f8fafc !important;
    }
    
    /* Ajuste de contraste da Barra Lateral (Sidebar) */
    [data-testid="stSidebar"] {
        background-color: #1e293b;
    }
    [data-testid="stSidebar"] * {
        color: #f8fafc !important;
    }
    
    /* Componente File Uploader */
    [data-testid="stFileUploaderDropzone"] {
        background-color: #1e293b !important;
        border: 2px dashed #475569 !important;
        border-radius: 8px !important;
    }
    
    /* Botão 'Browse files' */
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
    
    /* Textos do Uploader */
    [data-testid="stFileUploaderDropzone"] span, 
    [data-testid="stFileUploaderDropzone"] small,
    [data-testid="stFileUploaderFileData"] {
        color: #cbd5e1 !important;
    }
    
    /* Botão de Ação Principal */
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
    
    /* Caixas de Alerta/Informação */
    .stAlert {
        background-color: #1e293b !important;
        border: 1px solid #334155 !important;
    }
    </style>
""", unsafe_allow_html=True)

# Sidebar - Configuração da API Key
st.sidebar.title("⚙️ Configurações do Sistema")
api_key_input = st.sidebar.text_input(
    "Cole sua Gemini API Key:", 
    type="password"
)

st.sidebar.markdown("---")
st.sidebar.info("""
**Parâmetros Ativos de Auditoria:**
- Varredura Cronológica de Autos
- Qualificação da Medida Constritiva (Penhor x SISBAJUD)
- Retificação do Saldo Exequendo (IMR)
- Avaliação de Vulnerabilidade de Defesa
""")

# Cabeçalho
st.title("RISCO AG / FBC")
st.caption("Auditoria Jurídica Processual e Rating de Crédito do Agronegócio")

st.markdown("---")

# Layout Principal em Duas Colunas
col_left, col_right = st.columns([4, 8])

with col_left:
    st.subheader("Envio do Processo")
    uploaded_file = st.file_uploader("Arraste ou selecione o PDF integral dos autos:", type=["pdf"])
    
    btn_processar = st.button("Gerar Rating e Diagnóstico", disabled=(uploaded_file is None))

SYSTEM_INSTRUCTION = """
Você é um Auditor Jurídico de Elite especializado em Execuções de Agronegócio, Risco de Crédito e Contragarantias. Sua função é processar a íntegra dos autos de um processo judicial, realizar a varredura cronológica completa de todas as peças e emitir um Diagnóstico de Risco com Precisão Cirúrgica.

Ao analisar o conjunto documental do processo, você DEVE, obrigatoriamente, obedecer aos seguintes princípios operacionais:
1. LEITURA CRONOLÓGICA E HIERARQUIA DE EVENTOS.
2. QUALIFICAÇÃO PRECISA DA MEDIDA CONSTRITIVA PRINCIPAL.
3. MAPEAMENTO DINÂMICO DE STATUS E DILIGÊNCIAS.
4. CÁLCULO DE IMPACTO FINANCEIRO REAL (Materialidade / IMR).
5. ESTRUTURA DO DIAGNÓSTICO DE SAÍDA (Output):
   - Resumo Executivo do Caso
   - Objeto da Pretensão Primária vs. Secundária
   - Evolução do Saldo Devedor / Exposição Financeira
   - Cronologia dos Atos Processuais Relevantes e Decisões
   - Matriz de Risco Atualizada e Próximos Passos Recomendados
"""

with col_right:
    st.subheader("📊 Diagnóstico de Risco Processual")
    
    if btn_processar and uploaded_file is not None:
        clean_key = api_key_input.strip() if api_key_input else ""
        
        if not clean_key:
            st.error("Por favor, cole a sua Gemini API Key na barra lateral à esquerda para prosseguir.")
        else:
            temp_path = f"temp_{uploaded_file.name}"
            with open(temp_path, "wb") as f:
                f.write(uploaded_file.getbuffer())

            with st.spinner("Enviando e analisando autos via Gemini 3.6 Flash..."):
                try:
                    # Inicialização com passagem explícita da chave da API
                    client = genai.Client(api_key=clean_key)
                    
                    arquivo_processo = client.files.upload(file=temp_path)
                    
                    config = types.GenerateContentConfig(
                        system_instruction=SYSTEM_INSTRUCTION,
                        temperature=0.1,
                    )
                    
                    modelos = ["gemini-3.6-flash", "gemini-3.1-pro-preview"]
                    response = None
                    
                    for modelo in modelos:
                        try:
                            response = client.models.generate_content(
                                model=modelo,
                                contents=[
                                    arquivo_processo,
                                    "Realize o diagnóstico completo e cronológico deste processo judicial seguindo estritamente as instruções fornecidas.",
                                ],
                                config=config,
                            )
                            if response:
                                break
                        except APIError:
                            time.sleep(3)
                    
                    client.files.delete(name=arquivo_processo.name)
                    os.remove(temp_path)
                    
                    if response:
                        st.success("Auditoria concluída com sucesso!")
                        st.markdown(response.text)
                    else:
                        st.error("Ocorreu uma oscilação nos servidores do Google. Tente novamente em instantes.")
                        
                except Exception as e:
                    st.error(f"Erro no processamento: {str(e)}")
                    if os.path.exists(temp_path):
                        os.remove(temp_path)
    else:
        st.info("Aguardando upload de arquivo PDF para gerar a varredura e o relatório.")
